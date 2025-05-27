# Importación de bibliotecas y módulos necesarios:
# - streamlit: Framework para crear interfaces web interactivas
# - vector_store: Módulo personalizado para gestión de almacenes vectoriales
import streamlit as st
from vector_store import VectorStoreManager


@st.cache_resource  # Decorador de Streamlit para cachear recursos costosos
def load_embedding_model():
    """Función cacheada para cargar el modelo una sola vez
    
    Propósito:
        - Cargar el modelo de embeddings de manera eficiente
        - Evitar recargas innecesarias durante la sesión
        - Proporcionar feedback visual durante la carga
        
    Características:
        - Cacheada a nivel de recurso (persiste entre reruns)
        - Muestra spinner durante la carga
        - Maneja errores adecuadamente
        
    Returns:
        Modelo de embeddings cargado o None en caso de error
        
    Notas:
        - Usa el modelo 'all-MiniLM-L6-v2' de Sentence Transformers
        - La caché se mantiene mientras la app esté en ejecución
    """
    vs_manager = VectorStoreManager()  # Instancia del gestor de almacén vectorial
    model_name = "sentence-transformers/all-MiniLM-L6-v2"  # Modelo pre-entrenado de HuggingFace
    
    try:
        # Bloque de carga con feedback visual
        with st.spinner(f"🔍 Cargando modelo all-MiniLM-L6-v2 (solo una vez)..."):
            # Configura el modelo de embeddings a través del VectorStoreManager
            embed_model = vs_manager.setup_embeddings(model_name)
            print(f"Modelo {model_name} cargado correctamente")  # Log para depuración
            return embed_model
    except Exception as e:
        # Manejo de errores con mensaje claro en UI
        st.error(f"❌ Error al cargar el modelo: {e}")
        return None  # Retorno explícito para manejo de fallos


class ModelManager:
    """Maneja la carga y gestión del modelo de embeddings
    
    Responsabilidades:
        - Gestión centralizada del modelo de embeddings
        - Control del estado de carga del modelo
        - Proporcionar interfaz uniforme para acceder al modelo
        
    Atributos:
        - embed_model: Referencia al modelo cargado (None si no está cargado)
        - model_name: Nombre del modelo predefinido
        
    Patrones:
        - Singleton implícito (una instancia por app)
        - Lazy initialization (carga bajo demanda)
    """
    
    def __init__(self):
        """Inicializa el gestor de modelos
        
        Estado inicial:
            - Modelo no cargado (None)
            - Nombre del modelo predefinido
        """
        self.embed_model = None  # Modelo de embeddings (inicialmente no cargado)
        self.model_name = "sentence-transformers/all-MiniLM-L6-v2"  # Modelo por defecto
    
    def initialize_model(self):
        """Inicializa el modelo de embeddings
        
        Flujo:
            1. Llama a la función cacheada load_embedding_model()
            2. Almacena el modelo cargado en el atributo de instancia
            
        Returns:
            Modelo cargado o None si falló la carga
            
        Notas:
            - Aprovecha el caching de Streamlit para optimización
            - Solo realiza la carga real la primera vez
        """
        self.embed_model = load_embedding_model()  # Delegar la carga a la función cacheada
        return self.embed_model
    
    def get_model(self):
        """Obtiene el modelo actual
        
        Returns:
            Modelo de embeddings cargado o None
            
        Uso típico:
            - Para acceder al modelo en otras partes de la aplicación
            - Verificar disponibilidad antes de usarlo
            
        Consideraciones:
            - Puede devolver None si el modelo no se cargó correctamente
            - Los llamantes deben verificar el retorno
        """
        return self.embed_model
    
    def is_model_loaded(self) -> bool:
        """Verifica si el modelo está cargado
        
        Returns:
            bool: True si el modelo está cargado, False en caso contrario
            
        Propósito:
            - Permitir verificaciones rápidas de estado
            - Evitar intentar usar el modelo cuando no está disponible
            
        Ejemplo de uso:
            if model_manager.is_model_loaded():
                # Operaciones seguras con el modelo
        """
        return self.embed_model is not None  # Expresión booleana explícita
    
    def get_model_name(self) -> str:
        """Obtiene el nombre del modelo
        
        Returns:
            str: Nombre del modelo configurado
            
        Propósito:
            - Mostrar información del modelo en UI
            - Propósitos de logging y depuración
            - Consistencia en referencias al modelo
            
        Notas:
            - Siempre retorna el nombre, independientemente del estado de carga
        """
        return self.model_name