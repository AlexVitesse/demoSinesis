from typing import List, Dict, Optional
from datetime import datetime
import uuid
from pathlib import Path

# Importaciones para procesamiento de documentos
from langchain_core.documents import Document
from langchain_community.document_loaders import (
    PyMuPDFLoader,           # Loader para archivos PDF
    Docx2txtLoader,          # Loader para archivos DOCX
    TextLoader,              # Loader para archivos TXT
    CSVLoader,               # Loader para archivos CSV
    UnstructuredFileLoader   # Loader genérico para archivos no estructurados
)
from langchain.text_splitter import RecursiveCharacterTextSplitter
from config import clean_text  # Función personalizada para limpieza de texto

def load_document(file_path: str, file_type: str) -> List[Document]:
    """
    Carga un documento desde el sistema de archivos utilizando el loader
    adecuado según la extensión del archivo.

    Args:
        file_path (str): Ruta al archivo a cargar.
        file_type (str): Extensión del archivo (e.g., .pdf, .docx).

    Returns:
        List[Document]: Lista de documentos cargados con sus metadatos originales.
    """
    try:
        # Selección del loader adecuado según tipo de archivo
        if file_type == '.pdf':
            loader = PyMuPDFLoader(file_path)
        elif file_type == '.docx':
            loader = Docx2txtLoader(file_path)
        elif file_type == '.txt':
            loader = TextLoader(file_path)
        elif file_type == '.csv':
            loader = CSVLoader(file_path)
        else:
            # Loader genérico para otros tipos de archivo
            loader = UnstructuredFileLoader(file_path)
        
        return loader.load()
    except Exception as e:
        # En caso de error, se lanza una excepción informativa
        raise RuntimeError(f"Error al cargar el archivo {file_path}: {str(e)}")

def split_documents(docs: List[Document]) -> List[Document]:
    """
    Divide documentos en fragmentos o 'chunks' más pequeños para facilitar
    su análisis, manteniendo los metadatos originales.

    Args:
        docs (List[Document]): Lista de documentos a fragmentar.

    Returns:
        List[Document]: Lista de documentos fragmentados con metadatos.
    """
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,        # Tamaño máximo del chunk
        chunk_overlap=200,      # Número de caracteres que se sobrelapan entre chunks
        length_function=len,    # Función para calcular longitud del texto
        add_start_index=True    # Agrega el índice de inicio en los metadatos
    )
    
    # El splitter de LangChain ya maneja mantener los metadatos originales
    chunks = text_splitter.split_documents(docs)
    
    # Añadir metadatos por si el splitter no los genera
    for chunk in chunks:
        if 'start_index' not in chunk.metadata:
            chunk.metadata['start_index'] = 0  # Valor por defecto
    
    return chunks

def process_single_document(
    file_path: str, 
    file_type: str,
    additional_metadata: Optional[Dict] = None
) -> List[Document]:
    """
    Procesa un documento individual desde su carga hasta su división en chunks,
    enriqueciendo cada fragmento con metadatos útiles.

    Args:
        file_path (str): Ruta al archivo a procesar.
        file_type (str): Extensión del archivo (.pdf, .docx, etc.).
        additional_metadata (Optional[Dict]): Metadatos adicionales a incluir.

    Returns:
        List[Document]: Lista de chunks del documento con metadatos enriquecidos.
    """
    # 1. Cargar documento conservando metadatos originales
    docs = load_document(file_path, file_type)
    if not docs:
        return []  # Si no se cargó ningún documento, retornar lista vacía
    
    # 2. Preparar metadatos base del archivo
    file_metadata = {
        'source': file_path,  # Ruta del archivo
        'file_name': Path(file_path).name,  # Nombre del archivo
        'file_type': file_type.lower(),     # Tipo de archivo en minúsculas
        'file_size': f"{Path(file_path).stat().st_size / 1024:.2f} KB",  # Tamaño del archivo en KB
        'processing_time': datetime.now().isoformat(),  # Marca temporal del procesamiento
        'document_id': str(uuid.uuid4()),   # Identificador único del documento
    }
    
    # 3. Combinar con metadatos adicionales (si se proporcionan)
    if additional_metadata:
        file_metadata.update(additional_metadata)
    
    # 4. Limpiar contenido y actualizar metadatos
    for doc in docs:
        doc.page_content = clean_text(doc.page_content)  # Limpieza del texto
        # Fusionar metadatos: los originales del documento prevalecen
        doc.metadata = {**file_metadata, **doc.metadata}
    
    # 5. Dividir el documento en chunks
    chunks = split_documents(docs)
    
    # 6. Añadir metadatos adicionales a cada chunk
    for i, chunk in enumerate(chunks):
        chunk.metadata.update({
            'chunk_id': str(uuid.uuid4()),     # ID único del fragmento
            'chunk_number': i + 1,             # Número del chunk dentro del documento
            'total_chunks': len(chunks),       # Cantidad total de chunks
            'chunk_hash': hash(chunk.page_content)  # Hash para detectar duplicados
        })
        
        # Si el archivo es PDF y tiene metadatos de página, se agrega una etiqueta legible
        if file_type == '.pdf' and 'page' in chunk.metadata:
            chunk.metadata['page_label'] = f"Página {int(chunk.metadata['page']) + 1}"
    
    return chunks
