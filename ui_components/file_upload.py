# Importación de bibliotecas y módulos necesarios:
# - streamlit: Framework para crear interfaces web interactivas
# - typing: Para anotaciones de tipos (List, Dict)
# - file_manager: Módulo personalizado para manejo de archivos
# - document_db: Módulo personalizado para gestión de base de datos de documentos
import streamlit as st
from typing import List, Dict
from file_manager import FileManager
from document_db import DocumentDB
from youtube_processor import YouTubeProcessor


class FileUploadManager:
    """Maneja la interfaz de carga de archivos y videos de YouTube
    
    Responsabilidades principales:
    - Mostrar interfaz de carga de archivos o videos de YouTube
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
        self.youtube_processor = YouTubeProcessor()  # Procesador de YouTube
        
        # Inicializar session state para descargas de YouTube
        if 'downloads' not in st.session_state:
            st.session_state.downloads = []
        st.session_state.setdefault('resultado_dialogo', None)
    
    @st.dialog("Preview del video")
    def mostrar_video(self, url: str) -> None:
        """Muestra el video en un diálogo modal"""
        st.video(url)
        st.write("Cierra esta sección para volver.")
        if st.button("Cerrar", use_container_width=True):
            st.rerun()
    
    def show_file_upload(self):
        """Muestra la interfaz para carga de archivos o videos de YouTube
        
        Flujo principal:
            1. Configura la interfaz visual
            2. Permite seleccionar entre Documentos o Videos de YouTube
            3. Muestra la interfaz correspondiente según la selección
            4. Procesa archivos subidos o videos de YouTube
            5. Muestra vista previa y opciones
            
        Efectos secundarios:
            - Modifica el estado de la aplicación a través de DocumentDB
            - Crea/Mueve archivos en el sistema de archivos
            - Actualiza la interfaz de usuario
        """
        st.title("📤 Carga de Documentos")  # Título principal de la sección
        
        # Selector de categoría
        opcion_elegida = st.selectbox(
            "Selecciona una categoría",
            ("Documentos", "Videos de Youtube")
        )
        
        # Mostrar interfaz según la opción elegida
        if opcion_elegida == "Documentos":
            self._show_documents_upload()
        else:  # Videos de Youtube
            self._show_youtube_upload()
    
    def _show_documents_upload(self):
        """Muestra la interfaz para carga de documentos PDF, DOCX, TXT"""
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
    
    def _show_youtube_upload(self):
        """Muestra la interfaz para carga de videos de YouTube"""
        st.subheader("🎬 Cargar video de YouTube")
        
        url = st.text_input("Ingresa la URL del video de YouTube:")
        
        if url:
            try:
                # Obtener información del video
                info = self.youtube_processor.get_video_info(url)
                
                if info:
                    col1, col2 = st.columns([1, 2])
                    
                    with col1:
                        # Mostrar thumbnail
                        image_url = info.get('thumbnail')
                        button_key = "open_video_dialog_button"
                        
                        st.markdown(
                            f"""
                            <style>#{button_key} {{ display: none; }}</style>
                            <div onclick="document.getElementById('{button_key}').click()">
                                <img src="{image_url}" alt="Haz clic para ver el video" style="cursor: pointer; max-width: 100%; height: auto;">
                            </div>
                            """,
                            unsafe_allow_html=True
                        )
                        
                        if st.button("Abrir Video", key=button_key):
                            self.mostrar_video(url)
                        
                        # Información del video
                        st.caption(f"🕒 Duración: {self.youtube_processor.format_duration(info.get('duration'))}")
                        st.caption(f"👀 Vistas: {self.youtube_processor.format_views(info.get('view_count'))}")
                        st.caption(f"📅 Publicado: {self.youtube_processor.format_date(info.get('upload_date'))}")
                    
                    with col2:
                        # Título y canal
                        st.subheader(info.get('title', 'Sin título'))
                        st.caption(f"📺 Canal: {info.get('uploader', 'Desconocido')}")
                        
                        # Botón de descarga
                        # Botón de descarga optimizado
                        if st.button("Agregar Fuente", key="dl_subs", disabled=not self.embed_model):
                            try:
                                # Descargar subtítulos
                                sub_file = self.youtube_processor.download_subs(url)
                                if sub_file:
                                    # Procesar automáticamente sin mensajes intermedios
                                    self._process_youtube_subtitles(sub_file, info)
                                else:
                                    st.error("No se pudieron descargar los subtítulos del video")
                            except Exception as e:
                                st.error(f"Error al descargar subtítulos: {str(e)}")

            except Exception as e:
                st.error(str(e))
    
    def _register_youtube_file(self, sub_file: str, video_info: Dict):
        """Registra el archivo de subtítulos de YouTube en la base de datos
        
        Args:
            sub_file: Ruta del archivo de subtítulos descargado
            video_info: Información del video de YouTube
            
        Returns:
            Dict: Diccionario con los detalles del archivo registrado
        """
        try:
            # Registrar en la base de datos
            doc_id = self.db.add_document(
                sub_file,
                'txt',  # Tipo de archivo
                metadata={
                    'name': f"{video_info.get('title', 'Sin título')}_subtitulos.txt",
                    'source': 'youtube',
                    'video_url': video_info.get('webpage_url', ''),
                    'channel': video_info.get('uploader', 'Desconocido'),
                    'duration': video_info.get('duration', 0),
                    'upload_date': video_info.get('upload_date', ''),
                    'view_count': video_info.get('view_count', 0)
                }
            )
            
            # Crear detalle del archivo para procesamiento
            file_detail = {
                'doc_id': doc_id,
                'path': sub_file,
                'name': f"{video_info.get('title', 'Sin título')}_subtitulos.txt",
                'type': 'txt',
                'size': 0,  # Se podría calcular el tamaño del archivo
                'status': 'Procesando',  # Cambiar estado a procesando
                'source': 'youtube'
            }
            
            # Actualizar estado de archivos subidos
            uploaded_files_state = self.db.get_state("uploaded_files", [])
            uploaded_files_state.append(file_detail)
            self.db.set_state("uploaded_files", uploaded_files_state)
            
            return file_detail
            
        except Exception as e:
            st.error(f"Error al registrar el archivo: {str(e)}")
            return None
    
    def _process_youtube_subtitles(self, sub_file: str, video_info: Dict):
        """Procesa los subtítulos de YouTube usando el mismo flujo que los documentos regulares
        
        Args:
            sub_file: Ruta del archivo de subtítulos descargado
            video_info: Información del video de YouTube
        """
        try:
            with st.spinner("Procesando subtítulos y agregando a la base de vectores..."):
                # Registrar en la base de datos
                doc_id = self.db.add_document(
                    sub_file,
                    'txt',
                    metadata={
                        'name': f"{video_info.get('title', 'Sin título')}_subtitulos.txt",
                        'source': 'youtube',
                        'video_url': video_info.get('webpage_url', ''),
                        'channel': video_info.get('uploader', 'Desconocido'),
                        'duration': video_info.get('duration', 0),
                        'upload_date': video_info.get('upload_date', ''),
                        'view_count': video_info.get('view_count', 0)
                    }
                )
                
                # Crear estructura de archivo similar a los documentos subidos
                file_detail = {
                    'doc_id': doc_id,
                    'path': sub_file,
                    'name': f"{video_info.get('title', 'Sin título')}_subtitulos.txt",
                    'type': 'txt',
                    'size': 0,
                    'status': 'Procesando',
                    'source': 'youtube'
                }
                
                # Agregar al estado de archivos subidos
                uploaded_files_state = self.db.get_state("uploaded_files", [])
                uploaded_files_state.append(file_detail)
                self.db.set_state("uploaded_files", uploaded_files_state)
                
                # Preparar archivos para procesamiento
                valid_files = [(sub_file, 'txt')]
                files_to_process = [file_detail]
                
                # Procesar directamente sin mostrar interfaz adicional
                from ui_components.document_processor import DocumentProcessor
                processor = DocumentProcessor(self.db, self.embed_model)
                success = processor.process_and_save_files(valid_files, files_to_process)
                
                if success:
                    # Actualizar estado a completado
                    uploaded_files_state = self.db.get_state("uploaded_files", [])
                    for file in uploaded_files_state:
                        if file['path'] == sub_file:
                            file['status'] = 'Completado'
                            break
                    self.db.set_state("uploaded_files", uploaded_files_state)
                    
                    # Mostrar UN SOLO mensaje de éxito al final
                    st.success("✅ Subtítulos procesados y agregados a la base de vectores correctamente")
                    st.info("💡 Ahora puedes hacer consultas sobre el contenido de este video")
                else:
                    st.error("⚠️ Hubo un problema al procesar los subtítulos")
                        
        except Exception as e:
            st.error(f"Error al procesar subtítulos: {str(e)}")
            # Mostrar error más detallado para debugging
            st.error(f"Detalles del error: {type(e).__name__}: {e}")
            import traceback
            st.code(traceback.format_exc())

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
                        'upload_time': file['upload_time'],  # Marca temporal
                        'source': 'upload'  # Fuente del archivo
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