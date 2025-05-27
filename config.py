from pathlib import Path
import os
import time
import hashlib
from typing import List, Dict, Optional
from datetime import datetime

# Variables de sesión por defecto
DEFAULT_SESSION_STATE = {
    'uploaded_files': [],        # Lista de archivos subidos por el usuario
    'processed_docs': [],        # Lista de documentos ya procesados
    'chroma_dir': "chroma_db_dir",  # Directorio donde se almacenará la base de datos Chroma
    'collection_name': "document_collection",  # Nombre de la colección en el vector store
    'embed_model': None,         # Modelo de embedding (representación vectorial de textos)
    'vectorstore': None          # Almacén vectorial para búsqueda semántica
}

# --- Funciones de utilidad ---

def get_file_extension(file_name: str) -> str:
    """Obtiene la extensión del archivo en minúsculas"""
    return Path(file_name).suffix.lower()

def validate_file(file, max_size_mb: int = 10) -> bool:
    """
    Valida el tipo y tamaño del archivo.

    Args:
        file: Objeto archivo con atributos 'name' y 'size'.
        max_size_mb (int): Tamaño máximo permitido en megabytes (por defecto 10 MB).

    Returns:
        bool: True si el archivo es válido, de lo contrario lanza una excepción.

    Raises:
        ValueError: Si la extensión no es permitida o el tamaño excede el límite.
    """
    allowed_extensions = ['.pdf', '.docx', '.txt', '.csv']  # Tipos de archivo permitidos
    ext = get_file_extension(file.name)

    if ext not in allowed_extensions:
        raise ValueError(f"Tipo de archivo no soportado: {ext}")
    
    max_size = max_size_mb * 1024 * 1024  # Conversión de MB a bytes
    if file.size > max_size:
        raise ValueError(f"Archivo demasiado grande. Tamaño máximo: {max_size_mb}MB")
    
    return True

def generate_file_hash(content: bytes) -> str:
    """
    Genera un hash único para el archivo usando MD5.

    Args:
        content (bytes): Contenido binario del archivo.

    Returns:
        str: Hash MD5 en formato hexadecimal.
    """
    return hashlib.md5(content).hexdigest()

def clean_text(text: str) -> str:
    """
    Realiza una limpieza básica del texto.

    - Elimina espacios múltiples.
    - Elimina saltos de línea y tabulaciones.
    - Elimina espacios al inicio y al final.

    Args:
        text (str): Texto a limpiar.

    Returns:
        str: Texto limpio.
    """
    return ' '.join(text.split()).strip()
