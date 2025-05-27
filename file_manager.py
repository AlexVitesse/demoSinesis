# Importación de bibliotecas y módulos necesarios:
# - os: Para operaciones del sistema de archivos
# - pathlib: Para manejo de rutas multiplataforma
# - typing: Para anotaciones de tipos (List, Dict, Tuple, Optional)
# - datetime: Para manejo de marcas temporales
# - streamlit: Framework para interfaces web interactivas
# - config: Módulo personalizado con funciones auxiliares
import os
from pathlib import Path
from typing import List, Dict, Tuple, Optional
from datetime import datetime
import streamlit as st
from config import validate_file, generate_file_hash, get_file_extension

class FileManager:
    """Gestor de archivos para manejar operaciones de carga, validación y limpieza de documentos
    
    Responsabilidades:
    - Guardar archivos subidos en directorio temporal
    - Limpiar archivos temporales no necesarios
    - Validar y procesar archivos subidos
    - Mostrar vista previa de documentos
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

    def show_file_preview(self, file_details: List[Dict]) -> None:
        """Muestra vista previa de los archivos
        
        Args:
            file_details: Lista de diccionarios con metadatos de archivos
            
        Flujo:
            1. Muestra selector de archivos
            2. Lee y muestra contenido inicial del archivo seleccionado
            3. Maneja diferentes formatos de archivo
            
        Consideraciones:
            - Soporta diferentes estructuras de metadatos
            - Limita la lectura a 1000 caracteres para eficiencia
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
            file_names
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
            try:
                # Lectura segura del contenido (solo primeros 1000 caracteres)
                with open(selected_file["path"], "r", encoding='utf-8', errors='ignore') as f:
                    content = f.read(1000)
                    st.text_area("Contenido inicial", value=content, height=200)
            except UnicodeDecodeError:
                st.warning("No se puede previsualizar el contenido (archivo binario)")
            except Exception as e:
                st.error(f"Error al leer el archivo: {str(e)}")
        else:
            st.warning("No se pudo encontrar el archivo seleccionado")