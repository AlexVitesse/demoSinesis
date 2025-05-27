import streamlit as st
# Importar los nuevos componentes UI desde el módulo ui
# from ui import BaseUI, SidebarUI, FileUploadUI, DocumentManagerUI, SearchUI
from ui import UserInterface

# Configuración inicial de la página de Streamlit
st.set_page_config(
    page_title="Gestor de Base Vectorial",  # Título que se muestra en la pestaña del navegador
    page_icon="📚",                        # Ícono de la pestaña del navegador
    layout="wide"                         # Diseño de pantalla ancho
)

def main():
    # Crear una instancia de la interfaz de usuario principal
    ui = UserInterface()

    # Mostrar el contenido de la barra lateral (información, instrucciones, branding, etc.)
    ui.show_sidebar()
    
    # Diccionario que mapea las opciones del menú con sus respectivas funciones
    menu_options = {
        "Carga de Documentos": ui.show_file_upload,         # Interfaz para subir documentos
        "Gestión de Documentos": ui.show_document_manager,  # Herramientas para administrar documentos cargados
        "Búsqueda Semántica": ui.show_search_interface,     # Interfaz para realizar búsquedas inteligentes
        "Chat con Documentos": ui.show_chat_interface,         # Interfaz de chat para interactuar con documentos
    }
    
    # Mostrar el menú de navegación en la barra lateral
    selected_tab = st.sidebar.radio(
        "Navegación",                    # Etiqueta del menú
        list(menu_options.keys())       # Opciones del menú
    )
    
    # Llamar la función correspondiente a la opción seleccionada en el menú
    menu_options[selected_tab]()

# Punto de entrada del programa
# Verifica si el archivo está siendo ejecutado directamente
if __name__ == "__main__":
    main()
