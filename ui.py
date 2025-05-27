from typing import List, Dict
from config import DEFAULT_SESSION_STATE
from vector_store import VectorStoreManager
from file_manager import FileManager
from document_ui import DocumentUI
from document_db import DocumentDB

# Importar los nuevos componentes de UI modular
from ui_components.model_manager import ModelManager
from ui_components.sidebar import SidebarManager
from ui_components.file_upload import FileUploadManager
from ui_components.search_interface import SearchInterface
from ui_components.LLM.llm_interface import LlmInterface


class UserInterface:
    """Interfaz principal de usuario refactorizada en componentes modulares"""

    def __init__(self):
        # Inicializar gestores principales del sistema
        self.vs_manager = VectorStoreManager()      # Gestor de almacenamiento vectorial
        self.file_manager = FileManager()           # Gestor de archivos
        self.doc_ui = DocumentUI()                  # UI para gestión de documentos
        self.db = DocumentDB()                      # Gestor de base de datos de documentos

        # Inicializar el gestor del modelo de embeddings
        self.model_manager = ModelManager()
        self.embed_model = self.model_manager.initialize_model()  # Inicializa el modelo de embeddings

        # Inicializar componentes de interfaz de usuario (sidebar, upload, búsqueda)
        self._initialize_ui_components()

        # Inicializar el estado por defecto de la aplicación
        self._initialize_default_state()

        # Si el modelo de embeddings está cargado, registrar su nombre en la base de datos
        if self.embed_model:
            self.db.set_state("embed_model_name", self.model_manager.get_model_name())

    def _initialize_ui_components(self):
        """Inicializa los componentes de UI como barra lateral, carga de archivos y búsqueda"""
        self.sidebar_manager = SidebarManager(self.db, self.vs_manager, self.embed_model)
        self.file_upload_manager = FileUploadManager(self.db, self.file_manager, self.embed_model)
        self.search_interface = SearchInterface(self.db, self.vs_manager)
        self.llm_interface = LlmInterface(self.db, self.vs_manager, self.embed_model)

    def _initialize_default_state(self):
        """Inicializa el estado por defecto de la aplicación usando la configuración global"""
        for key, default_value in DEFAULT_SESSION_STATE.items():
            # Si el estado no existe, lo inicializa con el valor por defecto
            if self.db.get_state(key) is None:
                self.db.set_state(key, default_value)

    # Métodos de acceso directo para compatibilidad (uso general del estado)
    def _get_state(self, key, default=None):
        """Método de acceso al estado desde la base de datos"""
        return self.db.get_state(key, default)

    def _set_state(self, key, value):
        """Método de escritura al estado en la base de datos"""
        self.db.set_state(key, value)

    # Métodos principales que conectan la UI con cada componente modular
    def show_sidebar(self):
        """Delega la visualización de la barra lateral al componente SidebarManager"""
        self.sidebar_manager.show_sidebar()

    def show_file_upload(self):
        """Delega la funcionalidad de carga de archivos al componente FileUploadManager"""
        self.file_upload_manager.show_file_upload()

    def show_document_manager(self) -> None:
        """Muestra el panel para gestionar los documentos cargados"""
        documents = self.db.get_all_documents()  # (No se usa aquí directamente, puede usarse dentro del componente UI)
        self.doc_ui.show_document_manager()

    def show_search_interface(self) -> None:
        """Delega la visualización de la interfaz de búsqueda semántica"""
        self.search_interface.show_search_interface()
    
    def show_chat_interface(self) -> None:
        """Delega la visualización de la interfaz de chat con documentos"""
        self.llm_interface.show_llm_interface()

    # Métodos auxiliares para obtener información del estado del sistema
    def get_model_status(self) -> bool:
        """Devuelve True si el modelo de embeddings está cargado correctamente"""
        return self.model_manager.is_model_loaded()

    def get_vectorstore_stats(self) -> Dict:
        """Devuelve estadísticas del almacenamiento vectorial si existe"""
        if self._get_state("vectorstore_exists", False):
            return self.vs_manager.get_document_stats()
        return {}

    def get_database_stats(self) -> Dict:
        """Devuelve estadísticas sobre la base de datos de documentos"""
        return self.db.get_document_stats()
