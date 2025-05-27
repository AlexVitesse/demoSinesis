import os
import warnings
import logging
from typing import List, Dict, Optional
from pathlib import Path
import shutil

# Suprimir advertencias específicas de PyTorch/ChromaDB
warnings.filterwarnings("ignore", message=".*torch.classes.*")
warnings.filterwarnings("ignore", category=UserWarning, module="chromadb")

# Configurar logging para suprimir mensajes de ChromaDB
logging.getLogger("chromadb").setLevel(logging.ERROR)

from langchain_core.documents import Document
from langchain_core.embeddings import Embeddings
from langchain_chroma import Chroma
from langchain_huggingface import HuggingFaceEmbeddings

import torch


class VectorStoreManager:
    def __init__(self, chroma_dir: str = "BD/chroma_db_dir", collection_name: str = "document_collection"):
        """Inicializa el manejador del vectorstore, definiendo el directorio de persistencia y el nombre de la colección."""
        self.chroma_dir = chroma_dir
        self.collection_name = collection_name
        self.vectorstore: Optional[Chroma] = None
        
        # Suprimir advertencias específicas durante la inicialización
        self._suppress_torch_warnings()

    def _suppress_torch_warnings(self):
        """Suprime advertencias específicas de PyTorch que no afectan la funcionalidad."""
        import sys
        if not sys.warnoptions:
            warnings.simplefilter("ignore", category=UserWarning)
        
        # Configurar variables de entorno para suprimir advertencias de ChromaDB
        os.environ.setdefault("CHROMA_LOG_LEVEL", "ERROR")

    def setup_embeddings(self, model_name: str = "sentence-transformers/all-MiniLM-L6-v2") -> HuggingFaceEmbeddings:
        """Configura el modelo de embeddings usando langchain_huggingface, con detección automática de CUDA."""
        device = 'cuda' if torch.cuda.is_available() else 'cpu'
        
        # Suprimir advertencias durante la carga del modelo
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            return HuggingFaceEmbeddings(
                model_name=model_name,
                model_kwargs={'device': device},
                encode_kwargs={'normalize_embeddings': True}
            )

    def collection_exists(self) -> bool:
        """Verifica si existe una colección previamente guardada con documentos."""
        if not Path(self.chroma_dir).exists():
            return False

        try:
            # Se crea una instancia temporal para verificar si hay documentos
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                temp_store = Chroma(
                    persist_directory=self.chroma_dir,
                    collection_name=self.collection_name,
                    embedding_function=self.setup_embeddings()
                )
                return temp_store._collection.count() > 0
        except Exception as e:
            print(f"Error verificando colección existente: {e}")
            return False

    def load_vectorstore(self, embed_model: Embeddings) -> bool:
        """Carga el vectorstore existente si está disponible y lo asigna al atributo interno."""
        try:
            if self.collection_exists():
                with warnings.catch_warnings():
                    warnings.simplefilter("ignore")
                    self.vectorstore = Chroma(
                        embedding_function=embed_model,
                        persist_directory=self.chroma_dir,
                        collection_name=self.collection_name
                    )
                return True
            return False
        except Exception as e:
            print(f"Error cargando vectorstore: {e}")
            return False

    def save_to_chroma(self, docs: List[Document], embed_model: Embeddings = None, 
            document_name: str = "", document_type: str = "") -> Chroma:
        """Guarda una lista de documentos en ChromaDB, añadiendo metadatos útiles para identificación y trazabilidad."""
        if not docs:
            raise ValueError("No hay documentos para guardar")

        if embed_model is None:
            embed_model = self.setup_embeddings()

        # Generar un ID único para este batch
        import uuid
        from datetime import datetime
        batch_id = str(uuid.uuid4())
        
        # Enriquecer metadatos por documento
        for i, doc in enumerate(docs):
            if not hasattr(doc, 'metadata') or doc.metadata is None:
                doc.metadata = {}
                
            doc.metadata.update({
                "doc_id": f"doc_{batch_id}_{i}",
                "batch_id": batch_id,
                "document_name": document_name or Path(doc.metadata.get('source', 'unknown')).name,
                "document_type": document_type or Path(doc.metadata.get('source', '')).suffix[1:],
                "chunk_number": i + 1,
                "total_chunks": len(docs),
                "ingest_time": datetime.now().isoformat(),
                "embedding_model": getattr(embed_model, 'model_name', str(embed_model))
            })

        # Suprimir advertencias durante las operaciones de ChromaDB
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            
            # Si la colección ya existe, intenta agregar sin duplicar
            if self.collection_exists():
                if not self.vectorstore or not hasattr(self.vectorstore, '_embedding_function') or self.vectorstore._embedding_function is None:
                    self.vectorstore = Chroma(
                        persist_directory=self.chroma_dir,
                        collection_name=self.collection_name,
                        embedding_function=embed_model
                    )

                try:
                    # Obtener IDs existentes y filtrar duplicados
                    existing_ids = self.vectorstore.get()['ids']
                    new_docs = [doc for doc in docs if doc.metadata.get('doc_id') not in existing_ids]
                    
                    if new_docs:
                        self.vectorstore.add_documents(new_docs)
                except Exception as e:
                    print(f"Error al añadir documentos: {e}")
                    # Si falla, recrear la colección desde cero
                    self.vectorstore = Chroma.from_documents(
                        documents=docs,
                        embedding=embed_model,
                        persist_directory=self.chroma_dir,
                        collection_name=self.collection_name
                    )
            else:
                # Crear nueva colección con los documentos
                self.vectorstore = Chroma.from_documents(
                    documents=docs,
                    embedding=embed_model,
                    persist_directory=self.chroma_dir,
                    collection_name=self.collection_name
                )

        # Intentar persistir (aunque podría ser automático)
        try:
            if hasattr(self.vectorstore, 'persist'):
                self.vectorstore.persist()
        except Exception as e:
            print(f"Nota: No se pudo persistir explícitamente (esto podría ser normal): {e}")
            
        return self.vectorstore

    def get_document_stats(self, embed_model: Optional[Embeddings] = None) -> Dict[str, any]:
        """Devuelve estadísticas del vectorstore: número de chunks, dimensión del embedding, y metadatos de ejemplo."""
        if not embed_model:
            embed_model = self.setup_embeddings()
            
        if not self.vectorstore:
            self.load_vectorstore(embed_model)
            
        if not self.vectorstore:
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                self.vectorstore = Chroma(
                    embedding_function=embed_model,
                    persist_directory=self.chroma_dir,
                    collection_name=self.collection_name
                )

        try:
            stored_data = self.vectorstore.get()
            count = self.vectorstore._collection.count()
            test_embedding = embed_model.embed_query("Texto de prueba")
            embedding_dim = len(test_embedding)
            sample_metadatas = stored_data['metadatas'][:3] if count > 0 else []
            sample_ids = stored_data['ids'][:3] if count > 0 else []

            return {
                "total_chunks": count,
                "embedding_dim": embedding_dim,
                "sample_metadatas": sample_metadatas,
                "sample_ids": sample_ids,
                "metadata_fields": list(sample_metadatas[0].keys()) if sample_metadatas else []
            }
            
        except Exception as e:
            print(f"\n❌ Error al obtener estadísticas: {e}")
            return {
                "error": str(e),
                "total_chunks": 0,
                "embedding_dim": 0
            }

    def similarity_search(self, query: str, k: int = 5) -> List[tuple[Document, float]]:
        """Realiza búsqueda semántica usando embeddings y retorna los k documentos más similares."""
        if not self.vectorstore:
            raise ValueError("Vector store no inicializado. Llama a save_to_chroma() primero.")
        return self.vectorstore.similarity_search_with_score(query, k=k)

    def delete_documents(self, doc_ids: List[str]) -> None:
        """Elimina documentos específicos del vectorstore usando sus IDs."""
        if self.vectorstore:
            self.vectorstore.delete(doc_ids)
            self.vectorstore.persist()

    def persist(self) -> None:
        """Fuerza la persistencia del vectorstore en disco (si está soportado)."""
        if self.vectorstore:
            try:
                if hasattr(self.vectorstore, 'persist'):
                    self.vectorstore.persist()
            except Exception as e:
                print(f"Nota: No se pudo persistir explícitamente (esto podría ser normal): {e}")

    def clear_vectorstore(self) -> None:
        """Elimina completamente la base de datos local de Chroma, con soporte para Windows (manejo de archivos bloqueados)."""
        try:
            if self.vectorstore is not None:
                self.vectorstore = None
            
            import time
            time.sleep(1)  # Esperar para liberar handles de archivo
            
            if Path(self.chroma_dir).exists():
                if os.name == 'nt':
                    self._force_delete_windows(self.chroma_dir)
                else:
                    shutil.rmtree(self.chroma_dir)
            
            print(f"✅ Vectorstore en {self.chroma_dir} eliminado completamente")
        
        except Exception as e:
            print(f"❌ Error eliminando vectorstore: {e}")
            if os.name == 'nt':
                self._find_locking_processes(self.chroma_dir)

    def _force_delete_windows(self, path: str) -> None:
        """Utiliza comandos nativos de Windows para forzar la eliminación de un directorio."""
        import subprocess
        try:
            subprocess.run(f'rmdir /s /q "{path}"', shell=True, check=True)
        except subprocess.CalledProcessError:
            self._retry_delete(path, max_attempts=3)

    def _retry_delete(self, path: str, max_attempts: int = 3) -> None:
        """Reintenta la eliminación de un directorio varias veces, útil si hay bloqueos temporales."""
        import time
        for attempt in range(max_attempts):
            try:
                shutil.rmtree(path)
                return
            except PermissionError:
                time.sleep(2 ** attempt)
        raise PermissionError(f"No se pudo eliminar {path} después de {max_attempts} intentos")

    def _find_locking_processes(self, path: str) -> None:
        """[PENDIENTE DE IMPLEMENTACIÓN] Opcional: Identifica procesos que bloquean archivos en Windows."""
        pass  # Implementar con herramientas como 'handle.exe' o similar si es necesario