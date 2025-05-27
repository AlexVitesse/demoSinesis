# Importación de bibliotecas y módulos necesarios:
# - streamlit: Framework para crear interfaces web interactivas
# - pathlib: Para manejo de rutas de archivos de manera multiplataforma
# - vector_store: Módulo personalizado para gestión de almacenes vectoriales
# - document_db: Módulo personalizado para gestión de base de datos de documentos
import streamlit as st
from pathlib import Path
from vector_store import VectorStoreManager
from document_db import DocumentDB


class SearchInterface:
    """Maneja la interfaz de búsqueda semántica
    
    Responsabilidades principales:
    - Mostrar la interfaz de búsqueda al usuario
    - Recoger parámetros de búsqueda
    - Ejecutar búsquedas semánticas en el almacén vectorial
    - Presentar resultados de manera clara y organizada
    
    Dependencias:
    - Requiere instancias configuradas de DocumentDB y VectorStoreManager
    - Asume que el almacén vectorial ya contiene documentos indexados
    """
    
    def __init__(self, db: DocumentDB, vs_manager: VectorStoreManager):
        """Inicializa la interfaz de búsqueda
        
        Args:
            db (DocumentDB): Instancia de la base de datos para acceder a estados y metadatos
            vs_manager (VectorStoreManager): Gestor del almacén vectorial para realizar búsquedas
        """
        self.db = db  # Almacena referencia a la base de datos de documentos
        self.vs_manager = vs_manager  # Gestor del almacén vectorial
    
    def show_search_interface(self) -> None:
        """Muestra la interfaz de búsqueda
        
        Flujo principal:
            1. Verifica si hay documentos indexados
            2. Recoge parámetros de búsqueda del usuario
            3. Ejecuta y muestra resultados si hay consulta
            
        Efectos secundarios:
            - Modifica la interfaz de usuario mostrando widgets y resultados
            - Realiza llamadas al almacén vectorial para búsquedas
        """
        st.title("🔍 Búsqueda Semántica")  # Título principal de la sección
        
        # Verificación inicial de estado
        if not self._check_vectorstore_exists():
            st.warning("No hay documentos indexados para buscar")
            return  # Salida temprana si no hay documentos
        
        # Obtención de parámetros de búsqueda
        query, k = self._get_search_params()
        
        # Ejecución de búsqueda si hay consulta
        if query:
            self._perform_search(query, k)
    
    def _check_vectorstore_exists(self) -> bool:
        """Verifica si existe el vectorstore
        
        Returns:
            bool: True si hay documentos indexados, False en caso contrario
            
        Propósito:
            - Evitar búsquedas innecesarias cuando no hay datos
            - Proporcionar feedback claro al usuario
            
        Implementación:
            - Consulta el estado almacenado en la base de datos
            - Valor por defecto False si no existe el estado
        """
        return self.db.get_state("vectorstore_exists", False)
    
    def _get_search_params(self):
        """Obtiene los parámetros de búsqueda del usuario
        
        Returns:
            Tuple (query, k):
            - query: Texto de búsqueda ingresado por el usuario
            - k: Número de resultados a retornar (1-10)
            
        Widgets mostrados:
            - Campo de texto para consulta
            - Slider para seleccionar cantidad de resultados
            
        Consideraciones:
            - El placeholder guía al usuario sobre qué ingresar
            - El slider limita resultados para evitar sobrecarga
        """
        # Widget para ingresar texto de búsqueda
        query = st.text_input(
            "Ingresa tu consulta de búsqueda", 
            placeholder="Buscar en los documentos..."
        )
        # Widget para seleccionar cantidad de resultados
        k = st.slider("Número de resultados", min_value=1, max_value=10, value=3)
        
        return query, k
    
    def _perform_search(self, query: str, k: int):
        """Realiza la búsqueda y muestra los resultados
        
        Args:
            query (str): Texto de búsqueda ingresado por el usuario
            k (int): Cantidad de resultados a retornar
            
        Flujo:
            1. Muestra spinner durante la operación
            2. Delega la búsqueda al VectorStoreManager
            3. Muestra resultados o errores
            
        Manejo de errores:
            - Captura excepciones durante la búsqueda
            - Muestra mensaje de error claro al usuario
        """
        # Bloque de búsqueda con feedback visual
        with st.spinner("Buscando..."):
            try:
                # Ejecuta búsqueda semántica en el almacén vectorial
                results = self.vs_manager.similarity_search(query, k=k)
                # Muestra resultados formateados
                self._display_search_results(results)
                
            except Exception as e:
                st.error(f"Error en la búsqueda: {str(e)}")  # Feedback de error
    
    def _display_search_results(self, results):
        """Muestra los resultados de búsqueda
        
        Args:
            results: Lista de tuplas (documento, score) retornadas por la búsqueda
            
        Formato de visualización:
            - Resultados expandibles/collapsibles
            - Ordenados por relevancia (score)
            - Metadatos claros (nombre archivo, página)
            - Contenido legible
            
        Diseño:
            - Usa expanders para evitar saturar la pantalla
            - Muestra score de similitud con 2 decimales
            - Extrae nombre de archivo legible de la ruta
        """
        st.subheader("Resultados")  # Encabezado de sección
        
        # Iteración sobre resultados con índice
        for i, (doc, score) in enumerate(results):
            # Extracción y formateo del nombre de archivo
            source_path = doc.metadata.get('source', '')
            file_name = Path(source_path).name if source_path else 'Desconocido'
            
            # Contenedor expandible para cada resultado
            with st.expander(f"Resultado #{i+1} (Similitud: {score:.2f}) - {file_name}"):
                # Metadatos del documento
                st.write(f"**Página:** {doc.metadata.get('page', 'N/A')}")
                # Contenido principal con formato
                st.write(f"**Contenido:**\n{doc.page_content}")