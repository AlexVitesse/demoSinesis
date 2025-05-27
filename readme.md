# 🧠 RAG Expert Assistant

**RAG Expert Assistant** es una aplicación avanzada construida con arquitectura modular en Python que convierte documentos en asistentes expertos usando **Retrieval-Augmented Generation (RAG)**. Carga documentos de cualquier tema (PDF, TXT, DOCX, etc.) y obtén respuestas contextualizadas como si interactuaras con un experto en el contenido.

---

## 🚀 Características Principales

- 📄 **Carga múltiple de documentos** (PDF, TXT, DOCX, MD, etc.)
- 📦 **Almacenamiento vectorial inteligente** con ChromaDB
- 🧠 **Embeddings optimizados** con modelos Hugging Face
- 🔍 **Recuperación híbrida avanzada**: BM25 + Embeddings vectoriales
- 💬 **Chat interactivo contextual** con IA conversacional
- 🧱 **Arquitectura modular escalable** con componentes desacoplados
- 📊 **Estadísticas en tiempo real** de documentos y embeddings
- 🎛️ **Interfaz moderna** con Streamlit y componentes modulares
- 🔧 **Gestión inteligente de memoria** y optimización de recursos

---

## 🏗️ Arquitectura del Sistema

### Componentes Principales

- **`UserInterface`**: Orquestador principal de la aplicación
- **`VectorStoreManager`**: Gestión del almacenamiento vectorial
- **`FileManager`**: Procesamiento y carga de documentos
- **`DocumentUI`**: Interfaz de gestión de documentos
- **`DocumentDB`**: Persistencia de metadatos con SQLite
- **`RAGSystem`**: Motor principal de recuperación y generación

### Módulos UI Especializados

```
ui_components/
├── model_manager.py          # Gestión de modelos de embeddings
├── sidebar.py                # Navegación y configuración
├── file_upload.py            # Carga de archivos avanzada
├── search_interface.py       # Búsqueda semántica y por palabras clave
└── LLM/
    └── llm_interface.py      # Chat inteligente contextual
```

---

## 🛠️ Stack Tecnológico

| Categoría | Tecnología | Propósito |
|-----------|------------|-----------|
| **Frontend** | Streamlit | Interfaz web interactiva |
| **Base de Datos Vectorial** | ChromaDB | Almacenamiento de embeddings |
| **Procesamiento LLM** | LangChain + Groq | Cadenas de recuperación y generación |
| **Embeddings** | Hugging Face Transformers | Modelos de embeddings semánticos |
| **Búsqueda Híbrida** | BM25 + Vector Search | Recuperación precisa de contexto |
| **Base de Datos** | SQLite | Metadatos y estado de documentos |
| **Procesamiento** | PyPDF2, python-docx | Extracción de texto de documentos |

---

## 📋 Requisitos del Sistema

- **Python**: 3.9+ (recomendado 3.10+)
- **RAM**: Mínimo 4GB (recomendado 8GB+)
- **GPU**: Opcional (acelera embeddings)
- **Espacio**: 2GB+ libre para modelos y datos

---

## 🚀 Instalación y Configuración

### 1. Clonar el Repositorio

```bash
git clone https://github.com/tuusuario/demoSinesis.git
cd demoSinesis
```

### 2. Crear Entorno Virtual

```bash
python -m venv venv

# Windows
venv\Scripts\activate

# Linux/Mac
source venv/bin/activate
```

### 3. Instalar Dependencias

```bash
pip install -r requirements.txt
```

### 4. Configurar Variables de Entorno

Crea un archivo `.env` en la raíz del proyecto:

```env
# API Keys (elige uno o varios)
GROQ_API_KEY=tu_clave_groq_aqui
OPENAI_API_KEY=tu_clave_openai_aqui

# Configuración de Base de Datos
CHROMA_DB_PATH=BD/chroma_db_dir
SQLITE_DB_PATH=BD/documents.db

# Configuración de Modelos
EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2
LLM_MODEL=llama3-8b-8192
LLM_TEMPERATURE=0.7
```

### 5. Crear Estructura de Directorios

```bash
mkdir -p BD/chroma_db_dir
mkdir -p temp_uploads
```

---

## 🎯 Uso de la Aplicación

### Iniciar la Aplicación

```bash
streamlit run main.py
```

La aplicación se abrirá en `http://localhost:8501`

### Flujo de Trabajo

1. **📤 Carga de Documentos**
   - Usa el panel lateral para subir archivos
   - Soporta PDF, TXT, DOCX, MD
   - Visualiza el progreso de procesamiento

2. **🔍 Procesamiento Inteligente**
   - El sistema genera embeddings automáticamente
   - Crea índices vectoriales y BM25
   - Almacena metadatos en SQLite

3. **💬 Chat Contextual**
   - Haz preguntas en lenguaje natural
   - Obtén respuestas basadas en tus documentos
   - Ve las fuentes utilizadas para cada respuesta

4. **📊 Monitoreo**
   - Estadísticas de documentos cargados
   - Métricas de rendimiento
   - Estado del sistema vectorial

---

## 📁 Estructura del Proyecto

```
rag-expert-assistant/
├── main.py                     # 🚀 Punto de entrada principal
├── ui.py                       # 🖥️ Interfaz principal refactorizada
├── rag.py                      # 🧠 Motor RAG principal
├── config.py                   # ⚙️ Configuraciones globales
├── requirements.txt            # 📦 Dependencias Python
├── .env                        # 🔐 Variables de entorno
├── README.md                   # 📖 Documentación
│
├── BD/                         # 💾 Bases de datos
│   ├── chroma_db_dir/         # Almacenamiento vectorial
│   └── documents.db           # Metadatos SQLite
│
├── temp_uploads/              # 📁 Archivos temporales
│
├── ui_components/             # 🧩 Componentes modulares
│   ├── __init__.py
│   ├── model_manager.py       # Gestión de modelos
│   ├── sidebar.py             # Barra lateral
│   ├── file_upload.py         # Carga de archivos
│   ├── document_processor.py  # Procesamiento de documentos
│   ├── search_interface.py    # Interfaz de búsqueda
│   └── LLM/
│       ├── __init__.py
│       └── llm_interface.py   # Chat con IA
│
├── file_manager.py            # 📂 Gestión de archivos
├── document_ui.py             # 📄 UI de documentos
├── document_processing.py     # 🔄 Procesamiento de documentos
├── document_db.py             # 🗄️ Base de datos de documentos
└── vector_store.py            # 🔍 Gestión del almacén vectorial
```

---

## 🎪 Casos de Uso

### 🏢 Empresarial
- **Capacitación interna**: Manuales técnicos y políticas
- **Soporte técnico**: Bases de conocimiento inteligentes
- **Consultoría**: Análisis rápido de documentos contractuales

### 🎓 Académico/Investigación
- **Investigación científica**: Análisis de papers y publicaciones
- **Estudios jurídicos**: Consultas a leyes y reglamentos
- **Análisis documental**: Procesamiento de grandes volúmenes de texto

### 👨‍💼 Personal/Profesional
- **Gestión del conocimiento**: Organización de documentos personales
- **Aprendizaje**: Interacción con libros y materiales de estudio
- **Análisis de contenido**: Extracción de insights de documentos

---

## ⚡ Características Avanzadas

### 🔍 Búsqueda Híbrida
- **Búsqueda vectorial**: Similitud semántica avanzada
- **BM25**: Búsqueda por palabras clave tradicional
- **Ensemble**: Combinación ponderada de ambos métodos

### 🧠 IA Conversacional
- **Contexto dinámico**: Respuestas basadas en documentos cargados
- **Fuentes citadas**: Transparencia en las respuestas
- **Memoria de conversación**: Mantiene el contexto del chat

### 📊 Analíticas
- **Métricas de rendimiento**: Tiempo de respuesta y precisión
- **Estadísticas de uso**: Documentos más consultados
- **Monitoreo de recursos**: Uso de memoria y CPU

---

## 🔧 Configuración Avanzada

### Personalización de Modelos

```python
# En config.py
EMBEDDING_CONFIG = {
    "model_name": "sentence-transformers/all-MiniLM-L6-v2",
    "device": "cuda" if torch.cuda.is_available() else "cpu",
    "normalize_embeddings": True
}

LLM_CONFIG = {
    "model": "llama3-8b-8192",  # o "gpt-3.5-turbo"
    "temperature": 0.7,
    "max_tokens": 1024,
    "top_p": 0.9
}
```

### Optimización de Rendimiento

```python
# Configuración para documentos grandes
CHUNK_CONFIG = {
    "chunk_size": 1000,
    "chunk_overlap": 200,
    "separators": ["\n\n", "\n", ". ", " "]
}

# Configuración de recuperación
RETRIEVAL_CONFIG = {
    "vector_k": 8,
    "bm25_k": 8,
    "score_threshold": 0.3,
    "ensemble_weights": [0.6, 0.4]  # [vectorial, bm25]
}
```

---

## 🐛 Solución de Problemas

### Errores Comunes

#### `ModuleNotFoundError: No module named 'rag'`
```bash
# Verificar estructura de directorios
# Asegurar que existe ui_components/__init__.py
touch ui_components/__init__.py
touch ui_components/LLM/__init__.py
```

#### `ChromaDB collection not found`
```bash
# Limpiar y recrear base vectorial
rm -rf BD/chroma_db_dir
# Recargar documentos en la aplicación
```

#### `GROQ_API_KEY not found`
```bash
# Verificar archivo .env
echo "GROQ_API_KEY=tu_clave_aqui" >> .env
```

### Logs y Depuración

La aplicación genera logs detallados. Para habilitarlos:

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

---

## 🚧 Roadmap y Mejoras Futuras

### Versión 2.0
- [ ] **Multi-usuario**: Sesiones separadas por usuario
- [ ] **API REST**: Integración externa completa
- [ ] **Historial persistente**: Conversaciones guardadas
- [ ] **Análisis avanzado**: Dashboard de métricas

### Versión 2.1
- [ ] **Modelos locales**: Soporte para LLMs sin internet
- [ ] **Vectorización incremental**: Actualización sin recrear
- [ ] **Integración cloud**: AWS, GCP, Azure
- [ ] **Plugin system**: Extensiones personalizadas

---

## 🤝 Contribuciones

¡Las contribuciones son bienvenidas! Por favor:

1. Fork del repositorio
2. Crea una rama para tu feature (`git checkout -b feature/AmazingFeature`)
3. Commit tus cambios (`git commit -m 'Add some AmazingFeature'`)
4. Push a la rama (`git push origin feature/AmazingFeature`)
5. Abre un Pull Request

### Guías de Contribución
- Seguir PEP 8 para estilo de código
- Agregar docstrings a funciones nuevas
- Incluir tests para nuevas funcionalidades
- Actualizar documentación cuando sea necesario

---

## 📈 Métricas y Rendimiento

### Benchmarks Típicos
- **Carga de documento PDF (10 páginas)**: ~15-30 segundos
- **Generación de respuesta**: ~2-5 segundos
- **Búsqueda en 100 documentos**: ~200-500ms
- **Uso de memoria**: ~500MB-2GB (dependiendo del corpus)

### Optimizaciones Implementadas
- ✅ Cache de embeddings con LRU
- ✅ Lazy loading de modelos
- ✅ Batch processing para documentos múltiples
- ✅ Compresión de vectores con cuantización

---

## 📄 Licencia

Este proyecto está bajo la **Licencia MIT**. Ver el archivo [LICENSE](LICENSE) para más detalles.

```
MIT License

Copyright (c) 2025 RAG Expert Assistant

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software...
```

---

## 👨‍💻 Autor

**Alex** 🚀  
📍 **Campeche, México**  
🛠️ **Consultor TI | Especialista en Python & AI**  

### Conéctame
- 📧 Email: [eric.vazquez.condor@gmail.com](mailto:eric.vazquez.condor@gmail.com)
- 💼 LinkedIn: [Eric Vazquez](https://www.linkedin.com/in/eric-alejandro-vazquez-gongora-49342b148/l)
- 🐙 GitHub: [AlexVitesse](https://github.com/AlexVitesse)

---

## 🙏 Agradecimientos

- **LangChain**: Por el framework de LLM
- **ChromaDB**: Por la base de datos vectorial
- **Streamlit**: Por la interfaz web intuitiva  
- **Hugging Face**: Por los modelos de embeddings
- **Groq**: Por la API de inferencia rápida

---

## 📊 Estadísticas del Proyecto

![Python](https://img.shields.io/badge/Python-3.9+-blue.svg)
![Streamlit](https://img.shields.io/badge/Streamlit-1.28+-red.svg)
![LangChain](https://img.shields.io/badge/LangChain-0.1+-green.svg)
![License](https://img.shields.io/badge/License-MIT-yellow.svg)
![Status](https://img.shields.io/badge/Status-Active-brightgreen.svg)

---

<div align="center">

**⭐ Si este proyecto te ha sido útil, ¡no olvides darle una estrella! ⭐**

</div>