import sqlite3
from typing import List, Dict, Optional, Any, Tuple
from pathlib import Path
import uuid
import json
from datetime import datetime

class DocumentDB:
    def __init__(self, db_path: str = "BD/document_manager.db"):
        # Ruta al archivo de base de datos SQLite
        self.db_path = db_path
        self._init_db()  # Inicializa las tablas si no existen
    
    def _init_db(self) -> None:
        """Inicializa la base de datos con las tablas necesarias"""
        with self._get_connection() as conn:
            # Tabla para almacenar información básica de los documentos
            conn.execute("""
                CREATE TABLE IF NOT EXISTS documents (
                    id TEXT PRIMARY KEY,
                    path TEXT UNIQUE NOT NULL,
                    file_name TEXT NOT NULL,
                    file_type TEXT NOT NULL,
                    file_size TEXT NOT NULL,
                    status TEXT NOT NULL,
                    metadata TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
            """)
            #BORRAR TABLA processed_docs si existe
            
            
            
            # Tabla para mantener el estado de la aplicación (configuraciones, flags, etc.)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS app_state (
                    key TEXT PRIMARY KEY,
                    value TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
            """)
    
    def _get_connection(self) -> sqlite3.Connection:
        """Obtiene una conexión a la base de datos"""
        return sqlite3.connect(self.db_path)
    
    # Métodos para manejar el estado de la aplicación
    def set_state(self, key: str, value: Any) -> None:
        """Guarda un valor en el estado de la aplicación"""
        with self._get_connection() as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO app_state 
                (key, value, updated_at)
                VALUES (?, ?, ?)
                """,
                (key, json.dumps(value), datetime.now().isoformat())
            )
    
    def get_state(self, key: str, default: Optional[Any] = None) -> Any:
        """Obtiene un valor del estado de la aplicación"""
        with self._get_connection() as conn:
            cursor = conn.execute(
                "SELECT value FROM app_state WHERE key = ?", 
                (key,)
            )
            result = cursor.fetchone()
        
        # Devuelve el valor si existe, si no devuelve el valor por defecto
        return json.loads(result[0]) if result else default
    
    def delete_state(self, key: str) -> None:
        """Elimina un valor del estado de la aplicación"""
        with self._get_connection() as conn:
            conn.execute(
                "DELETE FROM app_state WHERE key = ?", 
                (key,)
            )

    # Métodos existentes para documentos (se mantienen igual)
    def add_document(self, file_path: str, file_type: str, metadata: Optional[Dict] = None) -> str:
        """Añade un nuevo documento a la base de datos"""
        doc_id = str(uuid.uuid4())  # Genera un ID único para el documento
        now = datetime.now().isoformat()  # Marca de tiempo actual
        
        with self._get_connection() as conn:
            conn.execute(
                """
                INSERT INTO documents 
                (id, path, file_name, file_type, file_size, status, metadata, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    doc_id,
                    file_path,
                    Path(file_path).name,  # Nombre del archivo
                    file_type.lower(),  # Tipo de archivo en minúsculas
                    f"{Path(file_path).stat().st_size / 1024:.2f} KB",  # Tamaño en KB
                    'Pendiente',  # Estado inicial del documento
                    json.dumps(metadata or {}),  # Metadatos serializados
                    now,
                    now
                )
            )
        return doc_id
    
    def update_document_status(self, file_path: str, status: str) -> None:
        """Actualiza el estado de un documento"""
        with self._get_connection() as conn:
            conn.execute(
                "UPDATE documents SET status = ?, updated_at = ? WHERE path = ?",
                (status, datetime.now().isoformat(), file_path)
            )
    
    def get_document(self, file_path: str) -> Optional[Dict]:
        """Obtiene un documento por su ruta"""
        with self._get_connection() as conn:
            cursor = conn.execute("SELECT * FROM documents WHERE path = ?", (file_path,))
            row = cursor.fetchone()
        
        return self._row_to_dict(row, 'documents') if row else None
    
    def get_all_documents(self, status_filter: Optional[str] = None) -> List[Dict]:
        """Obtiene todos los documentos con filtro opcional por estado"""
        query = "SELECT * FROM documents ORDER BY created_at DESC"
        params = ()
        
        if status_filter:
            query = "SELECT * FROM documents WHERE status = ? ORDER BY created_at DESC"
            params = (status_filter,)
        
        with self._get_connection() as conn:
            cursor = conn.execute(query, params)
            return [self._row_to_dict(row, 'documents') for row in cursor.fetchall()]
    
    def delete_document(self, file_path: str) -> None:
        """Elimina un documento y sus chunks procesados"""
        with self._get_connection() as conn:
            # Obtiene el ID del documento a eliminar
            cursor = conn.execute("SELECT id FROM documents WHERE path = ?", (file_path,))
            doc_id = cursor.fetchone()
            
            if doc_id:
                doc_id = doc_id[0]
                # Elimina los chunks asociados
                #conn.execute("DELETE FROM processed_docs WHERE document_id = ?", (doc_id,))
                # Elimina el documento
                conn.execute("DELETE FROM documents WHERE id = ?", (doc_id,))
    
    
    def clear_processed_chunks(self) -> None:
        """Elimina todos los chunks procesados"""
        with self._get_connection() as conn:
            conn.execute("DELETE FROM processed_docs")
    
    def _row_to_dict(self, row: Any, table: str) -> Dict:
        """Convierte una fila de la base de datos a un diccionario"""
        if table == 'documents':
            return {
                'id': row[0],
                'path': row[1],
                'file_name': row[2],
                'file_type': row[3],
                'file_size': row[4],
                'status': row[5],
                'metadata': json.loads(row[6]),
                'created_at': row[7],
                'updated_at': row[8]
            }
        elif table == 'processed_docs':
            return {
                'id': row[0],
                'document_id': row[1],
                'content': row[2],
                'metadata': json.loads(row[3]),
                'created_at': row[4]
            }
    
    def get_document_stats(self) -> Dict:
        """Obtiene estadísticas sobre los documentos almacenados"""
        stats = {}
        
        with self._get_connection() as conn:
            # Total de documentos en la base de datos
            cursor = conn.execute("SELECT COUNT(*) FROM documents")
            stats['total_documents'] = cursor.fetchone()[0]
            
            # Total de documentos agrupados por estado
            cursor = conn.execute(
                "SELECT status, COUNT(*) FROM documents GROUP BY status"
            )
            stats['documents_by_status'] = dict(cursor.fetchall())
            
            
        
        return stats
