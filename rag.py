import os
import warnings
from pathlib import Path
from typing import Dict, List, Optional, Any
import logging
import json
from functools import lru_cache

# Suprimir advertencias
warnings.filterwarnings("ignore", message=".*torch.classes.*")
warnings.filterwarnings("ignore", category=UserWarning, module="chromadb")

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Cambio a Ollama para uso local
from langchain_ollama import ChatOllama

# LangChain imports actualizados
from langchain_chroma import Chroma
from langchain_community.retrievers import BM25Retriever
from langchain.retrievers import EnsembleRetriever
from langchain_core.prompts import PromptTemplate
from langchain.chains import RetrievalQA
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_core.documents import Document

import torch


class RAGSystem:
    """
    Sistema RAG (Retrieval-Augmented Generation) para análisis de documentos.
    Permite cargar documentos de cualquier índole y responder preguntas basándose en su contenido.
    Soporta múltiples colecciones y utiliza recuperación híbrida (vectorial + BM25).
    """
    
    def __init__(self, 
                 collection_name: str = "document_collection",
                 chroma_dir: str = "BD/chroma_db_dir",
                 model_name: str = "llama3.1:8b",
                 temperature: float = 0.8,
                 ollama_base_url: str = "http://localhost:11434"):
        """
        Inicializa el sistema RAG con configuración personalizable.
        
        Args:
            collection_name: Nombre de la colección en ChromaDB
            chroma_dir: Directorio de la base de datos vectorial
            model_name: Modelo de Ollama a utilizar (ej: llama3.2, mistral, codellama)
            temperature: Temperatura para la generación
            ollama_base_url: URL base de Ollama (por defecto localhost:11434)
        """
        self.collection_name = collection_name
        self.chroma_dir = chroma_dir
        self.model_name = model_name
        self.temperature = temperature
        self.ollama_base_url = ollama_base_url
        
        # Inicializar componentes
        self._init_components()
        
        # Métricas
        self.total_tokens = 0
        self.total_cost = 0.0
        
        logger.info(f"✅ Sistema RAG inicializado para colección: '{collection_name}' con Ollama modelo: {model_name}")
    
    def _init_components(self):
        """Inicializa todos los componentes del sistema RAG."""
        try:
            self.llm = self._setup_llm()
            self.embed_model = self._setup_embeddings()
            self.vectorstore = self._load_vectorstore()
            self.retriever = self._setup_retriever()
            self.qa_chain = self._setup_qa_chain()
        except Exception as e:
            logger.error(f"Error inicializando componentes: {e}")
            raise
    
    def _setup_llm(self) -> ChatOllama:
        """Configura el modelo de lenguaje usando Ollama local."""
        try:
            return ChatOllama(
                model=self.model_name,
                base_url=self.ollama_base_url,
                temperature=self.temperature,
                top_p=0.9,
                num_predict=8192,  # Equivalente a max_output_tokens
                verbose=True
            )
        except Exception as e:
            logger.error(f"Error configurando LLM Ollama: {e}")
            logger.error(f"Asegúrate de que Ollama esté corriendo en {self.ollama_base_url}")
            logger.error(f"Y que el modelo '{self.model_name}' esté disponible (ollama pull {self.model_name})")
            raise

    def _setup_embeddings(self) -> HuggingFaceEmbeddings:
        """Configura el modelo de embeddings con optimizaciones."""
        device = 'cuda' if torch.cuda.is_available() else 'cpu'
        logger.info(f"Usando dispositivo para embeddings: {device}")
        
        try:
            return HuggingFaceEmbeddings(
                model_name="sentence-transformers/all-MiniLM-L6-v2",
                model_kwargs={'device': device},
                encode_kwargs={'normalize_embeddings': True}
            )
        except Exception as e:
            logger.error(f"Error configurando embeddings: {e}")
            raise
    
    def _load_vectorstore(self) -> Chroma:
        """Carga la base de datos vectorial existente."""
        if not Path(self.chroma_dir).exists():
            raise FileNotFoundError(
                f"Directorio de base vectorial no encontrado: {self.chroma_dir}. "
                "Por favor carga los documentos primero."
            )
        
        try:
            logger.info(f"📚 Cargando base vectorial desde: {self.chroma_dir}")
            
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                vectorstore = Chroma(
                    embedding_function=self.embed_model,
                    persist_directory=self.chroma_dir,
                    collection_name=self.collection_name
                )
            
            # Verificar que la colección tenga documentos
            count = vectorstore._collection.count()
            if count == 0:
                raise ValueError(f"La colección '{self.collection_name}' está vacía")
            
            logger.info(f"✅ Base vectorial cargada: {count} documentos en '{self.collection_name}'")
            
            # Obtener documentos para BM25
            stored_data = vectorstore.get()
            self.docs = stored_data['documents'] if stored_data['documents'] else []
            
            if not self.docs:
                logger.warning("No se encontraron documentos para BM25")
            
            return vectorstore
            
        except Exception as e:
            logger.error(f"Error cargando vectorstore: {e}")
            raise
    
    def _setup_retriever(self) -> EnsembleRetriever:
        """Configura el sistema de recuperación híbrida (vectorial + BM25) con más chunks."""
        try:
            # Recuperador vectorial con doble de chunks
            vector_retriever = self.vectorstore.as_retriever(
                search_type="similarity_score_threshold",
                search_kwargs={
                    "k": 16, # Aumentado de 8 a 16
                    "score_threshold": 0.3
                }
            )
            
            # Recuperador BM25 (solo si hay documentos)
            if self.docs:
                bm25_retriever = BM25Retriever.from_texts(self.docs)
                bm25_retriever.k = 16  # Aumentado de 8 a 16
                
                # Ensemble de ambos recuperadores
                ensemble_retriever = EnsembleRetriever(
                    retrievers=[vector_retriever, bm25_retriever],
                    weights=[0.6, 0.4]  # Más peso al vectorial
                )
                logger.info("✅ Recuperador híbrido (Vectorial + BM25) configurado con 16 chunks")
            else:
                ensemble_retriever = vector_retriever
                logger.info("✅ Recuperador vectorial configurado con 16 chunks (BM25 no disponible)")
            
            return ensemble_retriever
            
        except Exception as e:
            logger.error(f"Error configurando recuperador: {e}")
            # Fallback a solo vectorial con más chunks
            return self.vectorstore.as_retriever(search_kwargs={"k": 16})


    def _setup_qa_chain(self) -> RetrievalQA:
        """Configura la cadena de preguntas y respuestas."""
        prompt_template = """Eres un asistente inteligente especializado en analizar y responder preguntas basándote en documentos que han sido cargados previamente.

**Tu rol principal:**
- Analizar la información disponible en los documentos cargados
- Proporcionar respuestas precisas y útiles basadas en esa información
- Ser honesto cuando no tengas información suficiente
- Adaptar tu tono y nivel de detalle según la pregunta del usuario

**Información disponible en los documentos:**
{context}

**Instrucciones para responder:**
1. **Si encuentras información relevante**: Responde de manera clara y estructurada, citando los puntos clave
2. **Si la información es parcial**: Proporciona lo que puedas y menciona qué información adicional sería útil
3. **Si no hay información relevante**: Indica honestamente que no tienes datos sobre ese tema en los documentos cargados
4. **Siempre**: Mantén un tono profesional pero amigable

**Formato de respuesta preferido:**
- Respuesta directa a la pregunta
- Puntos clave organizados cuando sea necesario
- Menciona limitaciones si las hay

**Pregunta del usuario:**
{question}

**Respuesta basada en los documentos:**"""

        prompt = PromptTemplate(
            template=prompt_template,
            input_variables=['context', 'question']
        )
        print(prompt.input_variables)
        
        try:
            return RetrievalQA.from_chain_type(
                llm=self.llm,
                chain_type="stuff",
                retriever=self.retriever,
                return_source_documents=True,
                chain_type_kwargs={"prompt": prompt}
            )
        except Exception as e:
            logger.error(f"Error configurando cadena QA: {e}")
            raise
    
    #Generación de preguntas relacionadas
    def _generate_related_questions(self, original_question: str) -> List[str]:
        """
        Genera preguntas relacionadas para mejorar la recuperación de información.
        
        Args:
            original_question: Pregunta original del usuario
            
        Returns:
            Lista de preguntas relacionadas (incluyendo la original)
        """
        prompt_template = """Basándote en la pregunta original, genera exactamente 2 preguntas adicionales relacionadas que podrían ayudar a encontrar información complementaria en los documentos.

    Las preguntas adicionales deben:
    - Abordar aspectos diferentes pero relacionados con la pregunta original
    - Ser específicas y útiles para búsqueda de información
    - Cubrir posibles contextos o enfoques alternativos del tema

    Pregunta original: {question}

    Responde ÚNICAMENTE con las 2 preguntas adicionales, una por línea, sin numeración ni explicaciones adicionales."""

        try:
            prompt = PromptTemplate(
                template=prompt_template,
                input_variables=['question']
            )
            
            response = self.llm.invoke(prompt.format(question=original_question))
            
            # Procesar la respuesta para extraer las preguntas
            related_questions = []
            if hasattr(response, 'content'):
                lines = response.content.strip().split('\n')
                for line in lines:
                    line = line.strip()
                    if line and not line.startswith('-') and not line.startswith('*'):
                        # Limpiar numeración si existe
                        import re
                        clean_line = re.sub(r'^\d+\.\s*', '', line)
                        clean_line = re.sub(r'^[•\-\*]\s*', '', clean_line)
                        if clean_line:
                            related_questions.append(clean_line)
            
            # Limitar a 2 preguntas adicionales máximo
            related_questions = related_questions[:2]
            
            # Devolver la pregunta original más las relacionadas
            all_questions = [original_question] + related_questions
            
            logger.info(f"📝 Generadas {len(all_questions)} preguntas para búsqueda:")
            for i, q in enumerate(all_questions):
                logger.info(f"  {i+1}. {q[:60]}...")
            
            return all_questions
            
        except Exception as e:
            logger.error(f"Error generando preguntas relacionadas: {e}")
            # Fallback: devolver solo la pregunta original
            return [original_question]


    def ask_question(self, question: str) -> Dict[str, Any]:
        """
        Procesa una pregunta y devuelve una respuesta con fuentes.
        Utiliza múltiples preguntas relacionadas para mejorar la recuperación.
        
        Args:
            question: Pregunta del usuario
            
        Returns:
            Dict con 'answer', 'sources', 'metadata'
        """
        if not question.strip():
            return {
                "answer": "Por favor, hazme una pregunta específica sobre los documentos cargados.",
                "sources": [],
                "metadata": {"error": "Pregunta vacía"}
            }
        
        try:
            logger.info(f"🤔 Procesando pregunta: {question[:50]}...")
            
            # Generar preguntas relacionadas
            all_questions = self._generate_related_questions(question)
            
            # Recopilar documentos relevantes de todas las preguntas
            all_relevant_docs = []
            seen_content = set()  # Para evitar duplicados
            
            for q in all_questions:
                try:
                    docs = self.retriever.invoke(q)
                    for doc in docs:
                        # Usar hash del contenido para evitar duplicados
                        content_hash = hash(doc.page_content)
                        if content_hash not in seen_content:
                            seen_content.add(content_hash)
                            all_relevant_docs.append(doc)
                except Exception as e:
                    logger.warning(f"Error recuperando docs para pregunta '{q[:30]}...': {e}")
                    continue
            
            logger.info(f"📚 Recuperados {len(all_relevant_docs)} chunks únicos")
            
            # Construir contexto combinado
            context = "\n\n".join([doc.page_content for doc in all_relevant_docs])
            
            # Usar la pregunta original para generar la respuesta
            full_prompt = self.qa_chain.combine_documents_chain.llm_chain.prompt.format(
                context=context,
                question=question  # Solo la pregunta original
            )
            
            # Generar respuesta usando el LLM directamente
            response_obj = self.llm.invoke(full_prompt)
            
            if hasattr(response_obj, 'content'):
                answer = response_obj.content
            else:
                answer = str(response_obj)
            
            # Extraer fuentes únicas
            sources = []
            source_metadata = []
            
            for doc in all_relevant_docs:
                if hasattr(doc, 'metadata') and doc.metadata:
                    source_name = doc.metadata.get('source', 'Desconocido')
                    if source_name not in sources:
                        sources.append(source_name)
                        source_metadata.append({
                            'source': source_name,
                            'document_name': doc.metadata.get('document_name', 'Sin nombre'),
                            'chunk_number': doc.metadata.get('chunk_number', 0)
                        })
            
            result = {
                "answer": answer,
                "sources": sources,
                "metadata": {
                    "total_sources": len(sources),
                    "source_details": source_metadata,
                    "collection": self.collection_name,
                    "total_chunks_retrieved": len(all_relevant_docs),
                    "questions_used": len(all_questions)
                }
            }
            
            logger.info(f"✅ Respuesta generada con {len(sources)} fuentes y {len(all_relevant_docs)} chunks")
            return result
            
        except Exception as e:
            logger.error(f"❌ Error procesando pregunta: {str(e)}")
            return {
                "answer": "Disculpa, tuve un problema técnico procesando tu consulta. ¿Podrías reformular tu pregunta?",
                "sources": [],
                "metadata": {"error": str(e)}
            }

    def get_collection_info(self) -> Dict[str, Any]:
        """Devuelve información sobre la colección actual."""
        try:
            count = self.vectorstore._collection.count()
            return {
                "collection_name": self.collection_name,
                "total_documents": count,
                "chroma_directory": self.chroma_dir,
                "has_bm25": len(self.docs) > 0,
                "embedding_model": "all-MiniLM-L6-v2",
                "llm_model": self.model_name,
                "ollama_url": self.ollama_base_url
            }
        except Exception as e:
            logger.error(f"Error obteniendo info de colección: {e}")
            return {"error": str(e)}


class RAGSystemManager:
    """Gestor de múltiples instancias de RAG para diferentes colecciones de documentos."""
    
    _instances = {}
    
    @classmethod
    def get_rag_system(cls, 
                      collection_name: str = "document_collection",
                      chroma_dir: str = "BD/chroma_db_dir",
                      **kwargs) -> RAGSystem:
        """
        Obtiene una instancia de RAGSystem (patrón singleton por colección).
        
        Args:
            collection_name: Nombre de la colección
            chroma_dir: Directorio de ChromaDB
            **kwargs: Argumentos adicionales para RAGSystem
            
        Returns:
            Instancia de RAGSystem
        """
        key = f"{collection_name}_{chroma_dir}"
        
        if key not in cls._instances:
            logger.info(f"🚀 Creando nueva instancia RAG para: {collection_name}")
            cls._instances[key] = RAGSystem(
                collection_name=collection_name,
                chroma_dir=chroma_dir,
                **kwargs
            )
        
        return cls._instances[key]
    
    @classmethod
    def list_active_systems(cls) -> List[str]:
        """Lista los sistemas RAG activos."""
        return list(cls._instances.keys())
    
    @classmethod
    def clear_cache(cls):
        """Limpia el cache de instancias."""
        cls._instances.clear()
        logger.info("🧹 Cache de sistemas RAG limpiado")


# Funciones de conveniencia
def ask_question(question: str, 
                collection_name: str = "document_collection",
                chroma_dir: str = "BD/chroma_db_dir") -> str:
    """
    Función simple para hacer una pregunta y obtener solo la respuesta.
    
    Args:
        question: Pregunta del usuario
        collection_name: Nombre de la colección
        chroma_dir: Directorio de ChromaDB
        
    Returns:
        Respuesta como string
    """
    try:
        rag_system = RAGSystemManager.get_rag_system(collection_name, chroma_dir)
        result = rag_system.ask_question(question)
        return result["answer"]
    except Exception as e:
        logger.error(f"Error en ask_question: {e}")
        return f"Error: No se pudo procesar la pregunta. {str(e)}"


def ask_question_detailed(question: str,
                         collection_name: str = "document_collection", 
                         chroma_dir: str = "BD/chroma_db_dir") -> Dict[str, Any]:
    """
    Función para obtener respuesta detallada con metadatos y fuentes.
    
    Args:
        question: Pregunta del usuario
        collection_name: Nombre de la colección
        chroma_dir: Directorio de ChromaDB
        
    Returns:
        Dict completo con respuesta, fuentes y metadatos
    """
    try:
        rag_system = RAGSystemManager.get_rag_system(collection_name, chroma_dir)
        return rag_system.ask_question(question)
    except Exception as e:
        logger.error(f"Error en ask_question_detailed: {e}")
        return {
            "answer": f"Error: No se pudo procesar la pregunta. {str(e)}",
            "sources": [],
            "metadata": {"error": str(e)}
        }