import sqlite3
from typing import List, Dict, Optional, Any, Tuple
from pathlib import Path
import uuid
import json
import os
from datetime import datetime

class DocumentDB:
    def __init__(self, db_path: str = "BD/document_manager.db"):
        # Resuelve la ruta completa y crea directorios si no existen
        self.db_path = self._resolve_db_path(db_path)
        self._init_db()  # Inicializa las tablas si no existen
    
    def _resolve_db_path(self, db_path: str) -> str:
        """Resuelve la ruta de la base de datos y crea directorios necesarios"""
        # Convierte a Path para mejor manejo
        path = Path(db_path)
        
        # Si es una ruta relativa, la hace absoluta respecto al directorio actual
        if not path.is_absolute():
            path = Path.cwd() / path
        
        # Crea el directorio padre si no existe
        path.parent.mkdir(parents=True, exist_ok=True)
        
        # Verifica permisos de escritura en el directorio
        if not os.access(path.parent, os.W_OK):
            # Si no hay permisos, usa el directorio temporal del usuario
            fallback_path = Path.home() / ".demoSinesis" / "BD" / "document_manager.db"
            fallback_path.parent.mkdir(parents=True, exist_ok=True)
            print(f"⚠️ Sin permisos en {path.parent}, usando ruta alternativa: {fallback_path}")
            return str(fallback_path)
        
        return str(path)
    
    def _init_db(self) -> None:
        """Inicializa la base de datos con las tablas necesarias"""
        try:
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
                
                # Tabla para mantener el estado de la aplicación (configuraciones, flags, etc.)
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS app_state (
                        key TEXT PRIMARY KEY,
                        value TEXT NOT NULL,
                        updated_at TEXT NOT NULL
                    )
                """)
                
                # Confirma los cambios
                conn.commit()
                print(f"✅ Base de datos inicializada correctamente en: {self.db_path}")
                
        except sqlite3.Error as e:
            print(f"❌ Error al inicializar la base de datos: {e}")
            raise
    
    def _get_connection(self) -> sqlite3.Connection:
        """Obtiene una conexión a la base de datos"""
        try:
            # Configuraciones adicionales para mejor rendimiento y compatibilidad
            conn = sqlite3.connect(
                self.db_path,
                timeout=30.0,  # Timeout de 30 segundos
                check_same_thread=False  # Permite usar desde múltiples hilos
            )
            # Habilita foreign keys (buena práctica)
            conn.execute("PRAGMA foreign_keys = ON")
            return conn
        except sqlite3.Error as e:
            print(f"❌ Error al conectar con la base de datos: {e}")
            print(f"Ruta intentada: {self.db_path}")
            raise
    
    # Método para verificar la conexión
    def test_connection(self) -> bool:
        """Prueba la conexión a la base de datos"""
        try:
            with self._get_connection() as conn:
                cursor = conn.execute("SELECT name FROM sqlite_master WHERE type='table'")
                tables = cursor.fetchall()
                print(f"✅ Conexión exitosa. Tablas encontradas: {[t[0] for t in tables]}")
                return True
        except Exception as e:
            print(f"❌ Error en la conexión: {e}")
            return False
    
    # Método para obtener información del archivo de BD
    def get_db_info(self) -> Dict:
        """Obtiene información sobre el archivo de base de datos"""
        db_file = Path(self.db_path)
        
        info = {
            'path': str(db_file),
            'exists': db_file.exists(),
            'size': f"{db_file.stat().st_size / 1024:.2f} KB" if db_file.exists() else "0 KB",
            'writable': os.access(db_file.parent, os.W_OK),
            'parent_dir': str(db_file.parent),
            'parent_exists': db_file.parent.exists()
        }
        
        return info
    
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
        
        # Verifica que el archivo existe antes de agregarlo
        if not Path(file_path).exists():
            raise FileNotFoundError(f"El archivo {file_path} no existe")
        
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


# Función de utilidad para diagnosticar problemas
def diagnose_db_issues(db_path: str = "BD/document_manager.db"):
    """Función para diagnosticar problemas con la base de datos"""
    print("🔍 Diagnosticando problemas de base de datos...")
    print("-" * 50)
    
    # Información del directorio actual
    current_dir = Path.cwd()
    print(f"📁 Directorio actual: {current_dir}")
    print(f"📝 Permisos de escritura: {os.access(current_dir, os.W_OK)}")
    
    # Información de la ruta objetivo
    target_path = Path(db_path)
    if not target_path.is_absolute():
        target_path = current_dir / target_path
    
    print(f"🎯 Ruta objetivo: {target_path}")
    print(f"📁 Directorio padre: {target_path.parent}")
    print(f"📂 Directorio padre existe: {target_path.parent.exists()}")
    print(f"✍️  Permisos de escritura en directorio padre: {os.access(target_path.parent, os.W_OK)}")
    print(f"📄 Archivo existe: {target_path.exists()}")
    
    if target_path.exists():
        print(f"📏 Tamaño del archivo: {target_path.stat().st_size} bytes")
        print(f"✍️  Permisos de escritura en archivo: {os.access(target_path, os.W_OK)}")
    
    # Ruta alternativa
    fallback_path = Path.home() / ".demoSinesis" / "BD"
    print(f"🏠 Ruta alternativa: {fallback_path}")
    print(f"🏠 Home directory: {Path.home()}")
    
    print("-" * 50)
    
    try:
        # Intenta crear la base de datos
        print("🔧 Intentando crear/conectar base de datos...")
        db = DocumentDB(db_path)
        print("✅ Base de datos creada/conectada exitosamente!")
        
        # Muestra información de la BD
        info = db.get_db_info()
        print("📊 Información de la base de datos:")
        for key, value in info.items():
            print(f"   {key}: {value}")
            
        # Prueba la conexión
        db.test_connection()
        
    except Exception as e:
        print(f"❌ Error: {e}")
        print(f"🔧 Tipo de error: {type(e).__name__}")


if __name__ == "__main__":
    # Ejecuta el diagnóstico si se ejecuta directamente
    diagnose_db_issues()