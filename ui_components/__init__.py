"""
Componentes de interfaz de usuario modularizados.

Este paquete contiene los componentes especializados de la interfaz:
- ModelManager: Gestión del modelo de embeddings
- SidebarManager: Barra lateral con configuración
- FileUploadManager: Carga y manejo de archivos
- DocumentProcessor: Procesamiento de documentos
- SearchInterface: Interfaz de búsqueda semántica
"""

# Importación de los módulos que componen el paquete:
# - ModelManager y su función load_embedding_model del módulo model_manager
# - SidebarManager del módulo sidebar
# - FileUploadManager del módulo file_upload
# - DocumentProcessor del módulo document_processor
# - SearchInterface del módulo search_interface
# Estas importaciones permiten acceder a las clases y funciones directamente desde el paquete
from .model_manager import ModelManager, load_embedding_model
from .sidebar import SidebarManager
from .file_upload import FileUploadManager
from .document_processor import DocumentProcessor
from .search_interface import SearchInterface

# Lista __all__ que define qué símbolos se exportarán cuando se use 'from package import *'
# Esto es una buena práctica para:
# 1. Controlar explícitamente la API pública del paquete
# 2. Evitar la exportación de símbolos internos no deseados
# 3. Documentar qué componentes se consideran la interfaz pública estable
# Contiene:
# - ModelManager: Clase para gestionar modelos de embeddings
# - load_embedding_model: Función auxiliar para cargar modelos
# - SidebarManager: Clase para gestionar la barra lateral de la UI
# - FileUploadManager: Clase para manejar la carga de archivos
# - DocumentProcessor: Clase para procesamiento de documentos
# - SearchInterface: Clase principal para la interfaz de búsqueda semántica
__all__ = [
    'ModelManager',
    'load_embedding_model',
    'SidebarManager', 
    'FileUploadManager',
    'DocumentProcessor',
    'SearchInterface'
]