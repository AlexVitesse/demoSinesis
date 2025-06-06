# Importación de bibliotecas y módulos necesarios:
# - streamlit: Framework para crear interfaces web interactivas
# - vector_store: Módulo personalizado para gestión de almacenes vectoriales (ChromaDB)
# - document_db: Módulo personalizado para gestión de base de datos de documentos
import streamlit as st
from vector_store import VectorStoreManager
from document_db import DocumentDB


class SidebarManager:
    """Maneja la barra lateral con configuración y estadísticas
    
    Responsabilidades principales:
    - Mostrar estado del sistema y configuración
    - Proporcionar controles de configuración
    - Visualizar estadísticas de documentos y embeddings
    - Mostrar estado del modelo de embeddings
    
    Dependencias:
    - Requiere instancias configuradas de DocumentDB y VectorStoreManager
    - Necesita acceso al modelo de embeddings para mostrar su estado
    """

    def __init__(self, db: DocumentDB, vs_manager: VectorStoreManager, embed_model):
        """Inicializa el gestor de la barra lateral
        
        Args:
            db (DocumentDB): Instancia de la base de datos para acceder a estados y estadísticas
            vs_manager (VectorStoreManager): Gestor del almacén vectorial para obtener métricas
            embed_model: Modelo de embeddings para verificar estado de carga
            
        Efectos:
            - Almacena referencias a las dependencias necesarias
            - No realiza operaciones costosas durante inicialización
        """
        self.db = db  # Almacena referencia a la base de datos de documentos
        self.vs_manager = vs_manager  # Gestor del almacén vectorial (ChromaDB)
        self.embed_model = embed_model  # Modelo de embeddings para verificar estado

    def show_sidebar(self):
        """Muestra la barra lateral con opciones de configuración
        
        Flujo principal:
            1. Configura el contenedor de la barra lateral
            2. Muestra estado del modelo
            3. Muestra configuración de ChromaDB
            4. Muestra estadísticas del sistema
            
        Efectos secundarios:
            - Modifica el estado de la aplicación a través de DocumentDB
            - Actualiza la interfaz de usuario en la barra lateral
        """
        # Contexto de la barra lateral donde se renderizarán todos los elementos
        with st.sidebar:
            st.title("⚙️ Configuración")  # Título principal de la sección
            
            # Componentes de la barra lateral
            self._show_model_status()  # Estado del modelo de embeddings
            self._show_chroma_config()  # Configuración de ChromaDB
            self._show_statistics()  # Estadísticas del sistema

    def _show_model_status(self):
        """Muestra el estado del modelo de embeddings
        
        Propósito:
            - Proporcionar feedback visual sobre disponibilidad del modelo
            - Ayudar en diagnóstico de problemas cuando el modelo no está cargado
            
        Visualización:
            - Muestra éxito (verde) si el modelo está cargado
            - Muestra error (rojo) si el modelo no está disponible
            
        Consideraciones:
            - Asume que el modelo es 'all-MiniLM-L6-v2' cuando está cargado
            - No verifica validez del modelo, solo su existencia
        """
        st.subheader("Modelo de Embeddings")
        if self.embed_model:
            # Modelo cargado correctamente
            st.success("✅ all-MiniLM-L6-v2 (listo)")
        else:
            # Modelo no disponible
            st.error("❌ Modelo no cargado")

    def _show_chroma_config(self):
        """Muestra configuración de ChromaDB
        
        Flujo:
            1. Establece el directorio por defecto para ChromaDB
            2. Muestra input para nombre de colección
            3. Actualiza el estado con el valor ingresado
            
        Efectos secundarios:
            - Modifica el estado de la aplicación (collection_name)
            - Persiste el directorio de ChromaDB en el estado
            
        Consideraciones:
            - El directorio está hardcodeado por simplicidad
            - El nombre de colección se persiste entre sesiones
        """
        # Configuración fija del directorio de ChromaDB
        self.db.set_state("chroma_dir", "chroma_dir")
        
        # Input para nombre de colección con valor actual o por defecto
        #collection_name = st.text_input(
        #    "Nombre de colección", 
        #    value=self.db.get_state("collection_name")  # Valor actual o None
        #)
        # Persistencia del nuevo valor en el estado
        collection_name = "document_collection"
        self.db.set_state("collection_name", collection_name)

    def _show_statistics(self):
        """Muestra estadísticas del vectorstore
        
        Propósito:
            - Proporcionar métricas clave sobre los documentos indexados
            - Dar visibilidad del estado actual del sistema
            
        Métricas mostradas:
            - Cantidad total de documentos
            - Cantidad total de chunks/textos divididos
            - Dimensión de los embeddings
            
        Lógica:
            - Verifica existencia del vectorstore en estado o ChromaDB
            - Solo muestra estadísticas si hay datos indexados
            - Combina métricas de DocumentDB y VectorStoreManager
        """
        # Verificación de existencia del vectorstore (en estado o directamente en ChromaDB)
        vectorstore_exists = (
            self.db.get_state("vectorstore_exists", False)  # Estado en DocumentDB
            or self.vs_manager.collection_exists()  # Verificación directa en ChromaDB
        )
        
        # Solo mostrar estadísticas si existe el vectorstore
        if vectorstore_exists:
            # Obtención de estadísticas de diferentes fuentes
            stats = self.vs_manager.get_document_stats()  # Del almacén vectorial
            db_stats = self.db.get_document_stats()  # De la base de datos de documentos
            
            # Renderizado de las métricas
            st.subheader("📊 Estadísticas")
            # Documentos totales (de DocumentDB)
            st.write(f"📄 Documentos: {db_stats.get('total_documents', 0)}")
            # Chunks totales (del almacén vectorial)
            #st.write(f"✂️ Chunks: {stats.get('total_chunks', 0)}")
            # Dimensión de embeddings (del modelo)
            #st.write(f"🧮 Dimensión embeddings: {stats.get('embedding_dim', 0)}")