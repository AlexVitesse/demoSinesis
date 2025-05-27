# Importación de bibliotecas y módulos necesarios:
# - streamlit: Framework para crear interfaces web interactivas
# - time: Para manejo de marcas temporales
# - typing: Para anotaciones de tipos (List, Dict)
# - pathlib: Para manejo de rutas de archivos de manera multiplataforma
# - Módulos personalizados para procesamiento de documentos, almacenamiento vectorial y base de datos
import streamlit as st
import time
from typing import List, Dict
from pathlib import Path

from document_processing import process_single_document
from vector_store import VectorStoreManager
from document_db import DocumentDB


class DocumentProcessor:
    """Maneja el procesamiento y guardado de documentos
    
    Responsabilidades principales:
    - Procesamiento de documentos en diferentes formatos
    - Extracción y normalización de contenido
    - Almacenamiento en base de datos vectorial
    - Gestión de metadatos y estados
    """
    
    def __init__(self, db: DocumentDB, embed_model):
        """Inicializa el procesador de documentos
        
        Args:
            db (DocumentDB): Instancia de la base de datos para almacenar metadatos
            embed_model: Modelo de embeddings para convertir texto a vectores
            
        Dependencias:
            - Requiere una instancia configurada de DocumentDB
            - Necesita un modelo de embeddings cargado
        """
        self.db = db  # Almacena la referencia a la base de datos de documentos
        self.embed_model = embed_model  # Modelo para generar embeddings
        self.vs_manager = VectorStoreManager()  # Gestor del almacén vectorial
    
    def process_and_save_files(self, valid_files: List, file_details: List[Dict]) -> None:
        """Procesa y guarda los archivos en un solo paso
        
        Método principal que orquesta todo el flujo de procesamiento
        
        Args:
            valid_files: Lista de tuplas (ruta_archivo, tipo_archivo)
            file_details: Lista de diccionarios con metadatos de archivos
            
        Flujo:
            1. Verifica que el modelo de embeddings esté cargado
            2. Extrae rutas y tipos de archivos
            3. Procesa documentos en lote
            4. Almacena resultados en base vectorial
            
        Manejo de errores:
            - Valida presencia de modelo de embeddings
            - Captura y muestra errores durante el procesamiento
        """
        if not self.embed_model:
            st.error("Error: El modelo de embeddings no está cargado")
            return
        
        # Extracción de rutas y tipos de archivos para procesamiento
        file_paths = [f[0] for f in valid_files]  # Lista de rutas completas
        file_types = [f[1] for f in valid_files]  # Lista de extensiones/tipos
        
        # Bloque de procesamiento con indicador visual
        with st.spinner("Procesando y guardando documentos..."):
            processed_docs = self._process_documents(file_paths, file_types)
            
            if processed_docs:
                self._save_to_vectorstore(processed_docs, file_details, file_paths)
            else:
                st.warning("No se pudieron procesar documentos correctamente")
    
    def _process_documents(self, file_paths: List[str], file_types: List[str]) -> List:
        """Procesa los documentos individualmente
        
        Args:
            file_paths: Lista de rutas de archivos a procesar
            file_types: Lista de tipos correspondientes a cada archivo
            
        Returns:
            Lista de documentos procesados (normalmente objetos Document)
            
        Efectos secundarios:
            - Muestra progreso en la interfaz
            - Muestra advertencias/errores durante el procesamiento
            
        Consideraciones:
            - Procesamiento secuencial (podría optimizarse con threads para muchos archivos)
            - Manejo individual de cada archivo para evitar fallo total por error en uno
        """
        processed_docs = []
        progress_bar = st.progress(0)  # Barra de progreso inicializada
        status_text = st.empty()  # Contenedor para texto de estado dinámico
        
        # Procesamiento iterativo de cada archivo
        for i, (file_path, file_type) in enumerate(zip(file_paths, file_types)):
            # Actualización de UI con progreso actual
            status_text.text(f"Procesando archivo {i+1}/{len(file_paths)}: {Path(file_path).name}")
            progress_bar.progress((i + 1) / len(file_paths))
            
            try:
                # Obtención de metadatos y procesamiento del documento
                file_metadata = self._get_file_metadata(file_path, file_type)
                docs = process_single_document(file_path, file_type, additional_metadata=file_metadata)
                
                if docs:
                    processed_docs.extend(docs)
                else:
                    st.warning(f"No se extrajeron documentos de {Path(file_path).name}")
                    
            except Exception as e:
                st.error(f"Error al procesar archivo {Path(file_path).name}: {str(e)}")
                continue  # Continúa con siguiente archivo tras error
        
        # Limpieza de elementos de UI al finalizar
        status_text.empty()
        progress_bar.empty()
        return processed_docs
    
    def _get_file_metadata(self, file_path: str, file_type: str) -> Dict:
        """Genera metadatos para el archivo
        
        Args:
            file_path: Ruta completa del archivo
            file_type: Tipo/extensión del archivo
            
        Returns:
            Diccionario con metadatos estandarizados:
            - source: Ruta completa
            - file_name: Nombre del archivo
            - file_type: Tipo/extensión
            - upload_time: Marca temporal
            - file_size: Tamaño en KB
            
        Notas:
            - Usa pathlib para manejo seguro de rutas
            - Formatea el tamaño para legibilidad
        """
        return {
            'source': file_path,
            'file_name': Path(file_path).name,
            'file_type': file_type,
            'upload_time': time.strftime("%Y-%m-%d %H:%M:%S"),
            'file_size': f"{Path(file_path).stat().st_size / 1024:.2f} KB"
        }
    
    def _save_to_vectorstore(self, processed_docs: List, file_details: List[Dict], file_paths: List[str]):
        """Guarda los documentos procesados en ChromaDB y actualiza estados
        
        Args:
            processed_docs: Lista de documentos procesados
            file_details: Metadatos de los archivos originales
            file_paths: Rutas de los archivos procesados
            
        Flujo:
            1. Almacena documentos en ChromaDB
            2. Actualiza estado en base de datos
            3. Muestra estadísticas de éxito
            
        Manejo de errores:
            - Captura errores durante almacenamiento
            - Muestra mensaje detallado en UI
        """
        try:
            # Persistencia en almacén vectorial
            vectorstore = self.vs_manager.save_to_chroma(processed_docs, self.embed_model)
            self.db.set_state("vectorstore_exists", True)
            
            # Actualización de estados en UI y base de datos
            self._update_file_status(file_details, file_paths, processed_docs)
            
            # Feedback visual de éxito con estadísticas
            stats = self.vs_manager.get_document_stats()
            st.success(
                f"Procesados y guardados {len(processed_docs)} chunks de {len(file_paths)} documentos. "
                f"Total chunks: {stats.get('total_chunks', 0)}"
            )
            
        except Exception as e:
            st.error(f"Error en la finalización del procesamiento: {str(e)}")
    
    def _update_file_status(self, file_details: List[Dict], file_paths: List[str], processed_docs: List):
        """Actualiza el estado de los archivos procesados
        
        Args:
            file_details: Lista de metadatos de archivos
            file_paths: Rutas de archivos procesados
            processed_docs: Documentos resultantes
            
        Efectos:
            - Actualiza estado a "Indexado" en UI
            - Persiste estado en base de datos
            - Almacena chunks procesados
            
        Notas:
            - Maneja errores individuales por archivo
            - Mantiene consistencia entre UI y base de datos
        """
        # Actualización de estado en memoria para UI
        uploaded_files_state = self.db.get_state("uploaded_files", [])
        for file in file_details:
            file["status"] = "Indexado"
            
            try:
                self.db.update_document_status(file["path"], "Indexado")
            except Exception as db_error:
                st.error(f"Error al actualizar estado en BD: {str(db_error)}")
        
        self.db.set_state("uploaded_files", uploaded_files_state)
        
        # Persistencia de chunks en base de datos
        self._save_chunks_to_db(file_paths, processed_docs)
    
    def _save_chunks_to_db(self, file_paths: List[str], processed_docs: List):
        """Guarda los chunks procesados en la base de datos
        
        Args:
            file_paths: Rutas de archivos originales
            processed_docs: Documentos/chunks procesados
            
        Proceso:
            1. Recupera metadatos del documento original
            2. Filtra chunks pertenecientes a cada archivo
            3. Almacena relación documento-chunks
            
        Consideraciones:
            - Manejo de errores por archivo individual
            - Filtrado eficiente de chunks por fuente
        """
        for file_path in file_paths:
            try:
                # Recuperación de metadatos del documento original
                doc_info = self.db.get_document(file_path)
                if doc_info:
                    # Filtrado y formateo de chunks asociados
                    doc_chunks = [
                        {
                            'page_content': doc.page_content,
                            'metadata': doc.metadata
                        } 
                        for doc in processed_docs 
                        if doc.metadata.get('source') == file_path
                    ]
                    
                    # Persistencia si hay chunks válidos
                    if doc_chunks:
                        self.db.add_processed_chunks(doc_info['id'], doc_chunks)
                        
            except Exception as chunk_error:
                st.error(f"Error al guardar chunks para {Path(file_path).name}: {str(chunk_error)}")