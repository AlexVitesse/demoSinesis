# Importación de bibliotecas y módulos necesarios:
# - streamlit: Framework para crear interfaces web interactivas
# - typing: Para anotaciones de tipos (List, Dict)
# - file_manager: Módulo personalizado para manejo de archivos
# - document_db: Módulo personalizado para gestión de base de datos de documentos
import streamlit as st
from typing import List, Dict
from file_manager import FileManager
from document_db import DocumentDB


class FileUploadManager:
    """Maneja la interfaz de carga de archivos
    
    Responsabilidades principales:
    - Mostrar interfaz de carga de archivos
    - Validar y procesar archivos subidos
    - Coordinar con FileManager para manejo físico de archivos
    - Interactuar con DocumentDB para almacenar metadatos
    - Proporcionar feedback visual al usuario
    """
    
    def __init__(self, db: DocumentDB, file_manager: FileManager, embed_model):
        """Inicializa el gestor de carga de archivos
        
        Args:
            db (DocumentDB): Instancia de la base de datos para almacenar metadatos
            file_manager (FileManager): Gestor de operaciones con archivos físicos
            embed_model: Modelo de embeddings para procesamiento posterior
            
        Dependencias:
            - Requiere instancias configuradas de DocumentDB y FileManager
            - El modelo de embeddings puede ser None inicialmente
        """
        self.db = db  # Almacena referencia a la base de datos
        self.file_manager = file_manager  # Gestor de operaciones con archivos
        self.embed_model = embed_model  # Modelo para generación de embeddings
    
    def show_file_upload(self):
        """Muestra la interfaz para carga de archivos
        
        Flujo principal:
            1. Configura la interfaz visual
            2. Limpia archivos temporales previos
            3. Muestra el widget de carga
            4. Procesa archivos subidos
            5. Muestra vista previa y opciones
            
        Efectos secundarios:
            - Modifica el estado de la aplicación a través de DocumentDB
            - Crea/Mueve archivos en el sistema de archivos
            - Actualiza la interfaz de usuario
        """
        st.title("📤 Carga de Documentos")  # Título principal de la sección
        
        # Obtiene el estado actual de archivos subidos o inicializa lista vacía
        uploaded_files_state = self.db.get_state("uploaded_files", [])
        
        # Limpieza de archivos temporales de cargas previas
        # Evita acumulación de archivos no procesados
        self.file_manager.clean_temp_files(uploaded_files_state)
        
        # Widget de Streamlit para carga de archivos:
        # - Soporta múltiples archivos
        # - Filtra por extensiones permitidas
        # - Almacena temporalmente los archivos en memoria
        uploaded_files = st.file_uploader(
            "Sube tus documentos (PDF, DOCX, TXT)",
            type=["pdf", "docx", "txt"],
            accept_multiple_files=True
        )
        
        # Si se subieron archivos, procesarlos
        if uploaded_files:
            # Procesamiento inicial y validación de archivos
            valid_files, file_details = self._handle_file_upload(
                uploaded_files, uploaded_files_state
            )
            
            # Si hay archivos válidos, mostrar interfaz de procesamiento
            if valid_files:
                self._show_upload_interface(valid_files, file_details, uploaded_files_state)
    
    def _handle_file_upload(self, uploaded_files, uploaded_files_state):
        """Procesa los archivos subidos
        
        Args:
            uploaded_files: Lista de archivos subidos a través de Streamlit
            uploaded_files_state: Estado actual de archivos en la aplicación
            
        Returns:
            Tuple (valid_files, file_details):
            - valid_files: Lista de tuplas (ruta, tipo) de archivos válidos
            - file_details: Lista de diccionarios con metadatos de archivos
            
        Efectos secundarios:
            - Guarda archivos físicamente a través de FileManager
            - Actualiza la base de datos con nuevos documentos
            - Modifica el estado de la aplicación
        """
        # Delegar el manejo físico de archivos al FileManager
        valid_files, file_details = self.file_manager.handle_uploaded_files(
            uploaded_files, uploaded_files_state
        )
        
        # Si hay archivos válidos, registrar en la base de datos
        if file_details:
            # Registrar cada archivo en la base de datos
            for file in file_details:
                # Insertar documento con sus metadatos básicos
                doc_id = self.db.add_document(
                    file['path'],  # Ruta física del archivo
                    file['type'],  # Tipo/extensión del archivo
                    metadata={
                        'name': file['name'],  # Nombre original
                        'size': file['size'],  # Tamaño del archivo
                        'upload_time': file['upload_time']  # Marca temporal
                    }
                )
                file['doc_id'] = doc_id  # Guardar ID asignado
            
            # Actualizar estado global de archivos subidos
            uploaded_files_state.extend(file_details)
            self.db.set_state("uploaded_files", uploaded_files_state)
        
        return valid_files, file_details
    
    def _show_upload_interface(self, valid_files, file_details, uploaded_files_state):
        """Muestra la interfaz de archivos a procesar
        
        Args:
            valid_files: Lista de archivos válidos para procesar
            file_details: Metadatos detallados de los archivos
            uploaded_files_state: Estado completo de archivos en la app
            
        Flujo:
            1. Muestra vista previa de archivos
            2. Habilita botón de procesamiento
            3. Inicia procesamiento al hacer click
            
        Consideraciones:
            - Importación dinámica de DocumentProcessor para evitar circular imports
            - Deshabilita botón si no hay modelo de embeddings cargado
        """
        # Determinar qué archivos mostrar en vista previa:
        # Prioriza los nuevos, sino muestra pendientes del estado actual
        files_to_preview = file_details if file_details else [
            f for f in uploaded_files_state 
            if f['status'] == 'Pendiente' and f['path'] in [vf[0] for vf in valid_files]
        ]
        # Mostrar vista previa usando FileManager
        self.file_manager.show_file_preview(files_to_preview)
        
        # Botón de procesamiento con estado condicional:
        # - Deshabilitado si no hay modelo de embeddings
        # - Estilo primario para destacar acción principal
        if st.button("Procesar y Guardar", disabled=not self.embed_model):
            # Determinar qué archivos procesar (similar a vista previa)
            files_to_process = file_details if file_details else [
                f for f in uploaded_files_state 
                if f['status'] == 'Pendiente' and f['path'] in [vf[0] for vf in valid_files]
            ]
            
            # Importación dinámica para evitar dependencia circular:
            # DocumentProcessor también podría necesitar FileUploadManager
            from ui_components.document_processor import DocumentProcessor
            # Crear instancia del procesador y ejecutar
            processor = DocumentProcessor(self.db, self.embed_model)
            processor.process_and_save_files(valid_files, files_to_process)