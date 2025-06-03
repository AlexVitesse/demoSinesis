# Importación de bibliotecas y módulos necesarios:
# - os: Para operaciones del sistema de archivos
# - pathlib: Para manejo de rutas multiplataforma
# - typing: Para anotaciones de tipos (List, Dict, Tuple, Optional)
# - datetime: Para manejo de marcas temporales
# - streamlit: Framework para interfaces web interactivas
# - streamlit_pdf_viewer: Para visualización mejorada de PDFs
# - config: Módulo personalizado con funciones auxiliares
import os
from pathlib import Path
from typing import List, Dict, Tuple, Optional
from datetime import datetime
import streamlit as st
from streamlit_pdf_viewer import pdf_viewer
from config import validate_file, generate_file_hash, get_file_extension

class FileManager:
    """Gestor de archivos para manejar operaciones de carga, validación y limpieza de documentos
    
    Responsabilidades:
    - Guardar archivos subidos en directorio temporal
    - Limpiar archivos temporales no necesarios
    - Validar y procesar archivos subidos
    - Mostrar vista previa de documentos con soporte mejorado para PDF
    """
    
    def __init__(self):
        """Inicializa el FileManager creando el directorio temporal si no existe"""
        self.temp_dir = "temp_uploads"  # Directorio para almacenamiento temporal
        os.makedirs(self.temp_dir, exist_ok=True)  # Crea el directorio si no existe
        
    def save_uploaded_file(self, uploaded_file) -> Optional[str]:
        """Guarda un archivo subido en el directorio temporal y devuelve su ruta
        
        Args:
            uploaded_file: Archivo subido a través de Streamlit (UploadedFile object)
            
        Returns:
            str: Ruta del archivo guardado o None si falla
            
        Flujo:
            1. Valida el archivo usando config.validate_file()
            2. Guarda el archivo en el directorio temporal
            3. Retorna la ruta o None si hay error
            
        Manejo de errores:
            - Muestra mensaje de error en UI si falla
            - Retorna None para manejo de fallos
        """
        try:
            # Validación inicial del archivo
            if not validate_file(uploaded_file):
                return None
                
            # Construcción de ruta de guardado    
            file_path = os.path.join(self.temp_dir, uploaded_file.name)
            # Escritura del contenido del archivo
            with open(file_path, "wb") as f:
                f.write(uploaded_file.getbuffer())
            return file_path
        except Exception as e:
            st.error(f"Error al guardar archivo: {str(e)}")
            return None

    def clean_temp_files(self, uploaded_files: List[Dict]) -> None:
        """Elimina archivos temporales de documentos ya procesados
        
        Args:
            uploaded_files: Lista de diccionarios con estado de archivos subidos
            
        Lógica:
            - Mantiene archivos con estado 'Pendiente' o 'Procesado'
            - Elimina archivos temporales que ya no son necesarios
            
        Manejo de errores:
            - Muestra error por archivo fallido pero continúa con los demás
        """
        # Archivos a conservar (pendientes o procesados)
        temp_files_to_keep = [f['path'] for f in uploaded_files if f['status'] in ['Pendiente', 'Procesado']]
        
        # Revisión de archivos en directorio temporal
        for filename in os.listdir(self.temp_dir):
            file_path = os.path.join(self.temp_dir, filename)
            # Eliminar archivos no listados para conservar
            if file_path not in temp_files_to_keep:
                try:
                    os.remove(file_path)
                except Exception as e:
                    st.error(f"Error al eliminar archivo temporal {file_path}: {str(e)}")

    def handle_uploaded_files(self, uploaded_files, existing_files: List[Dict]) -> Tuple[List[Tuple[str, str]], List[Dict]]:
        """Procesa los archivos subidos y devuelve los válidos y sus detalles
        
        Args:
            uploaded_files: Archivos subidos a través de Streamlit
            existing_files: Lista de archivos ya registrados
            
        Returns:
            Tuple[List[Tuple[str, str]], List[Dict]]:
            - Lista de archivos válidos (ruta, extensión)
            - Lista de metadatos de nuevos archivos
            
        Flujo:
            1. Valida cada archivo
            2. Verifica duplicados mediante hash
            3. Guarda archivos temporales
            4. Prepara metadatos para nuevos archivos
            
        Manejo de errores:
            - Omite archivos inválidos
            - Muestra advertencias para duplicados
            - Muestra errores individuales sin detener el proceso
        """
        valid_files = []  # Archivos válidos para procesar
        new_file_details = []  # Metadatos de nuevos archivos
        
        for file in uploaded_files:
            try:
                if validate_file(file):
                    file_content = file.getvalue()
                    file_hash = generate_file_hash(file_content)  # Hash único del contenido
                    
                    # Verificar si el archivo ya fue indexado completamente
                    existing_file = next((f for f in existing_files 
                                        if f['hash'] == file_hash and f['status'] == 'Indexado'), None)
                    
                    if not existing_file:
                        # Guardar archivo temporalmente
                        file_path = self.save_uploaded_file(file)
                        if not file_path:
                            continue
                        
                        valid_files.append((file_path, get_file_extension(file.name)))
                        
                        # Buscar archivo existente no indexado
                        unindexed_file = next((f for f in existing_files 
                                             if f['hash'] == file_hash and f['status'] != 'Indexado'), None)
                        
                        if unindexed_file:
                            # Actualizar archivo existente no indexado
                            unindexed_file.update({
                                "path": file_path,
                                "upload_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                                "status": "Pendiente"
                            })
                        else:
                            # Crear metadatos para nuevo archivo
                            new_file_details.append({
                                "name": file.name,
                                "size": f"{round(file.size / (1024 * 1024), 2)} MB",
                                "type": get_file_extension(file.name),
                                "hash": file_hash,
                                "path": file_path,
                                "upload_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                                "status": "Pendiente"
                            })
                    else:
                        st.warning(f"El archivo {file.name} ya fue cargado e indexado anteriormente")
            except Exception as e:
                st.error(str(e))
        
        return valid_files, new_file_details

    def _is_pdf_file(self, file_path: str) -> bool:
        """Verifica si un archivo es PDF basándose en su extensión
        
        Args:
            file_path: Ruta del archivo
            
        Returns:
            bool: True si es archivo PDF, False en caso contrario
        """
        return Path(file_path).suffix.lower() == '.pdf'

    def _show_pdf_preview(self, file_path: str, file_name: str) -> None:
        """Muestra vista previa de archivo PDF usando streamlit-pdf-viewer
        
        Args:
            file_path: Ruta del archivo PDF
            file_name: Nombre del archivo para mostrar
        """
        try:
            st.info(f"📄 Vista previa de: **{file_name}**")
            
            # Configuración básica del visualizador PDF (parámetros compatibles)
            with open(file_path, "rb") as pdf_file:
                pdf_data = pdf_file.read()
                
            # Usar solo parámetros básicos para máxima compatibilidad
            pdf_viewer(
                input=pdf_data,
                width=700,
                height=600,
                key=f"pdf_viewer_{hash(file_name)}"  # Usar hash para evitar caracteres especiales
            )
            
        except Exception as e:
            st.error(f"Error al mostrar PDF: {str(e)}")
            # Intentar con parámetros mínimos
            try:
                st.warning("Intentando con configuración básica...")
                with open(file_path, "rb") as pdf_file:
                    pdf_data = pdf_file.read()
                pdf_viewer(pdf_data)
            except Exception as e2:
                st.error(f"Error con configuración básica: {str(e2)}")
                # Fallback final a información básica
                st.warning("Mostrando información básica del archivo:")
                st.text(f"Archivo: {file_name}")
                st.text(f"Tipo: PDF")
                st.text(f"Ubicación: {file_path}")
                
                # Mostrar opción de descarga
                try:
                    with open(file_path, "rb") as pdf_file:
                        st.download_button(
                            label="📥 Descargar PDF",
                            data=pdf_file.read(),
                            file_name=file_name,
                            mime="application/pdf"
                        )
                except Exception:
                    pass

    def _show_text_preview(self, file_path: str, file_name: str) -> None:
        """Muestra vista previa de archivos de texto
        
        Args:
            file_path: Ruta del archivo
            file_name: Nombre del archivo para mostrar
        """
        try:
            # Lectura segura del contenido (solo primeros 1000 caracteres)
            with open(file_path, "r", encoding='utf-8', errors='ignore') as f:
                content = f.read(1000)
                if len(content) == 1000:
                    content += "\n\n... (contenido truncado para previsualización)"
                st.text_area("Contenido inicial", value=content, height=200)
        except UnicodeDecodeError:
            st.warning("No se puede previsualizar el contenido (archivo binario)")
        except Exception as e:
            st.error(f"Error al leer el archivo: {str(e)}")

    def show_file_preview(self, file_details: List[Dict]) -> None:
        """Muestra vista previa de los archivos con soporte mejorado para PDF
        
        Args:
            file_details: Lista de diccionarios con metadatos de archivos
            
        Flujo:
            1. Muestra selector de archivos
            2. Detecta el tipo de archivo (PDF vs otros)
            3. Usa el visor apropiado según el tipo
            4. Maneja diferentes formatos de archivo
            
        Consideraciones:
            - Soporta diferentes estructuras de metadatos
            - Usa streamlit-pdf-viewer para PDFs
            - Mantiene compatibilidad con archivos de texto
            - Maneja archivos binarios y errores de codificación
        """
        if not file_details:
            return
            
        st.subheader("📝 Vista Previa de Documentos")
        
        # Construcción de lista de nombres de archivo considerando diferentes estructuras
        file_names = []
        for f in file_details:
            if 'name' in f:  # Para archivos recién subidos
                file_names.append(f["name"])
            elif 'file_name' in f:  # Para documentos de la base de datos
                file_names.append(f["file_name"])
            else:  # Como último recurso usar el path
                file_names.append(Path(f["path"]).name)
        
        # Selector de archivos para previsualización
        preview_file = st.selectbox(
            "Selecciona un archivo para previsualizar",
            file_names,
            help="Los archivos PDF se mostrarán con un visor interactivo"
        )
        
        # Búsqueda del archivo seleccionado
        selected_file = None
        for f in file_details:
            if ('name' in f and f['name'] == preview_file) or \
               ('file_name' in f and f['file_name'] == preview_file) or \
               (Path(f['path']).name == preview_file):
                selected_file = f
                break
        
        if selected_file:
            file_path = selected_file["path"]
            
            # Verificar si el archivo existe
            if not os.path.exists(file_path):
                st.error(f"El archivo no se encuentra en la ruta: {file_path}")
                return
            
            # Mostrar información del archivo
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Tipo", selected_file.get('type', 'Desconocido'))
            with col2:
                if 'size' in selected_file:
                    st.metric("Tamaño", selected_file['size'])
            with col3:
                if 'upload_time' in selected_file:
                    st.metric("Subido", selected_file['upload_time'])
            
            st.divider()
            
            # Mostrar vista previa según el tipo de archivo
            if self._is_pdf_file(file_path):
                self._show_pdf_preview(file_path, preview_file)
            else:
                st.info(f"📄 Vista previa de: **{preview_file}**")
                self._show_text_preview(file_path, preview_file)
        else:
            st.warning("No se pudo encontrar el archivo seleccionado")

    def get_pdf_files(self, file_details: List[Dict]) -> List[Dict]:
        """Retorna solo los archivos PDF de la lista
        
        Args:
            file_details: Lista de diccionarios con metadatos de archivos
            
        Returns:
            List[Dict]: Lista filtrada con solo archivos PDF
        """
        return [f for f in file_details if self._is_pdf_file(f.get('path', ''))]

    def show_pdf_gallery(self, file_details: List[Dict]) -> None:
        """Muestra una galería de todos los archivos PDF
        
        Args:
            file_details: Lista de diccionarios con metadatos de archivos
        """
        pdf_files = self.get_pdf_files(file_details)
        
        if not pdf_files:
            st.info("No hay archivos PDF para mostrar en la galería")
            return
        
        st.subheader("🖼️ Galería de PDFs")
        
        # Mostrar PDFs in pestañas
        if len(pdf_files) > 1:
            tab_names = [Path(f['path']).name for f in pdf_files]
            tabs = st.tabs(tab_names)
            
            for tab, pdf_file in zip(tabs, pdf_files):
                with tab:
                    self._show_pdf_preview(pdf_file['path'], Path(pdf_file['path']).name)
        else:
            # Solo un PDF, mostrarlo directamente
            pdf_file = pdf_files[0]
            self._show_pdf_preview(pdf_file['path'], Path(pdf_file['path']).name)