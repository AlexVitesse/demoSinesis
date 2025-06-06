import streamlit as st
from typing import List, Dict, Optional
import pandas as pd
from document_db import DocumentDB

class DocumentUI:
    def __init__(self, db_path: str = "BD/document_manager.db"):
        # Inicializa la interfaz y crea una instancia de la base de datos
        self.db = DocumentDB(db_path)
    
    def show_document_manager(self) -> None:
        """Muestra el panel principal de administración de documentos"""
        st.title("📂 Gestión de Documentos")
        
        # Obtener documentos desde la base de datos
        uploaded_files = self.db.get_all_documents()
        
        if not uploaded_files:
            st.info("No hay documentos cargados aún")
            return
        
        # Extrae los tipos de documentos de los archivos cargados
        document_types = []
        for f in uploaded_files:
            doc_type = f.get("file_type", "Desconocido")
            document_types.append(doc_type)
        
        # Sección de filtros por tipo y estado de documento
        col1, col2, col3 = st.columns(3)
        with col1:
            filter_type = st.selectbox(
                "Filtrar por tipo",
                ["Todos"] + list(set(document_types))
            )
        with col2:
            filter_status = st.selectbox(
                "Filtrar por estado",
                ["Todos", "Pendiente", "Procesado", "Indexado"]
            )
        with col3:
            # Botón para refrescar los datos mostrados
            if st.button("🔄 Refrescar"):
                st.rerun()
        
        # Mostrar estadísticas generales de los documentos
        self._show_document_stats()
        
        # Mostrar tabla de documentos con los filtros seleccionados
        self._show_documents_table(uploaded_files, filter_type, filter_status)
    
    def _show_document_stats(self) -> None:
        """Muestra estadísticas resumidas de los documentos almacenados"""
        stats = self.db.get_document_stats()
        
        # Mostrar estadísticas en cuatro columnas
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Total Documentos", stats.get('total_documents', 0))
        #with col2:
        #    st.metric("Total Chunks", stats.get('total_chunks', 0))
        with col2:
            pendientes = stats.get('documents_by_status', {}).get('Pendiente', 0)
            st.metric("Pendientes", pendientes)
        with col3:
            procesados = stats.get('documents_by_status', {}).get('Procesado', 0)
            st.metric("Procesados", procesados)
    
    def _show_documents_table(self, uploaded_files: List[Dict], filter_type: str, filter_status: str) -> None:
        """Muestra la tabla de documentos con filtros aplicados"""
        filtered_files = []
        for f in uploaded_files:
            # Verifica si coincide el tipo
            type_matches = filter_type == "Todos"
            if not type_matches:
                doc_type = f.get("file_type", "Desconocido")
                type_matches = doc_type == filter_type
            
            # Verifica si coincide el estado
            status_matches = filter_status == "Todos"
            if not status_matches:
                doc_status = f.get("status", "Pendiente")
                status_matches = doc_status == filter_status
            
            # Añadir a la lista si cumple ambos filtros
            if type_matches and status_matches:
                filtered_files.append(f)
        
        st.subheader("Documentos Cargados")
        if filtered_files:
            # Prepara los datos para mostrarlos en un DataFrame
            table_data = []
            for f in filtered_files:
                table_row = {
                    "name": f.get("file_name", "Sin nombre"),
                    "type": f.get("file_type", "Desconocido"),
                    "size": f.get("file_size", "Desconocido"),
                    "status": f.get("status", "Pendiente"),
                    "created_at": f.get("created_at", "Desconocido"),
                    "path": f.get("path", "")
                }
                table_data.append(table_row)
            
            # Mostrar solo las columnas principales
            df = pd.DataFrame(table_data)
            df_display = df[["name", "type", "size", "status", "created_at"]]
            
            # Mostrar la tabla de documentos
            st.dataframe(
                df_display,
                column_config={
                    "name": "Nombre",
                    "type": "Tipo",
                    "size": "Tamaño",
                    "status": "Estado",
                    "created_at": "Fecha de carga"
                },
                hide_index=True,
                use_container_width=True
            )
            
            # Interfaces para eliminar o actualizar documentos
            self._show_delete_documents_interface(filtered_files)
            self._show_update_status_interface(filtered_files)
        else:
            st.info("No hay documentos que coincidan con los filtros")
    
    def _show_delete_documents_interface(self, filtered_files: List[Dict]) -> None:
        """Muestra la interfaz para eliminar documentos seleccionados"""
        st.subheader("🗑️ Eliminar Documentos")
        
        # Mapeo de nombre de documento a su ruta
        doc_options = {}
        for f in filtered_files:
            doc_name = f.get("file_name", "Sin nombre")
            doc_path = f.get("path", "")
            doc_options[doc_name] = doc_path
        
        # Multiselección de documentos a eliminar
        docs_to_delete = st.multiselect(
            "Selecciona documentos para eliminar",
            list(doc_options.keys())
        )
        
        if docs_to_delete:
            st.warning(f"⚠️ Esto eliminará permanentemente {len(docs_to_delete)} documento(s) y todos sus chunks procesados.")
            
            col1, col2 = st.columns(2)
            with col1:
                if st.button("🗑️ Confirmar eliminación", type="primary"):
                    try:
                        # Elimina cada documento seleccionado de la base de datos
                        for doc_name in docs_to_delete:
                            doc_path = doc_options[doc_name]
                            self.db.delete_document(doc_path)
                        
                        st.success(f"✅ Se eliminaron {len(docs_to_delete)} documentos correctamente")
                        st.rerun()
                    except Exception as e:
                        st.error(f"❌ Error al eliminar documentos: {str(e)}")
            
            with col2:
                if st.button("❌ Cancelar"):
                    st.rerun()
    
    def _show_update_status_interface(self, filtered_files: List[Dict]) -> None:
        """Permite actualizar el estado de un documento seleccionado"""
        st.subheader("📝 Actualizar Estado")
        
        # Lista desplegable con estado actual en el nombre
        doc_options = {}
        for f in filtered_files:
            doc_name = f.get("file_name", "Sin nombre")
            doc_path = f.get("path", "")
            current_status = f.get("status", "Pendiente")
            doc_options[f"{doc_name} (Estado actual: {current_status})"] = doc_path
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            selected_doc = st.selectbox(
                "Seleccionar documento",
                ["Ninguno"] + list(doc_options.keys())
            )
        
        with col2:
            new_status = st.selectbox(
                "Nuevo estado",
                ["Pendiente", "Procesado", "Indexado", "Error"]
            )
        
        with col3:
            if selected_doc != "Ninguno" and st.button("🔄 Actualizar Estado"):
                try:
                    doc_path = doc_options[selected_doc]
                    self.db.update_document_status(doc_path, new_status)
                    st.success(f"✅ Estado actualizado a '{new_status}'")
                    st.rerun()
                except Exception as e:
                    st.error(f"❌ Error al actualizar estado: {str(e)}")
    
    def show_document_details(self, document_id: str) -> None:
        """Muestra detalles de un documento, incluyendo sus chunks procesados"""
        st.subheader("📄 Detalles del Documento")
        
        # Obtener los chunks procesados del documento
        chunks = self.db.get_processed_chunks(document_id)
        
        if chunks:
            st.info(f"Este documento tiene {len(chunks)} chunks procesados")
            
            # Mostrar hasta los primeros 3 chunks con su contenido y metadatos
            with st.expander("Ver contenido de chunks"):
                for i, chunk in enumerate(chunks[:3]):
                    st.write(f"**Chunk {i+1}:**")
                    st.text_area(
                        f"Contenido del chunk {i+1}",
                        chunk.get('content', ''),
                        height=100,
                        disabled=True
                    )
                    st.json(chunk.get('metadata', {}))
                
                if len(chunks) > 3:
                    st.info(f"... y {len(chunks) - 3} chunks más")
        else:
            st.warning("Este documento no tiene chunks procesados aún")
    
    def clear_all_processed_data(self) -> None:
        """Interfaz para eliminar todos los chunks procesados de todos los documentos"""
        st.subheader("🧹 Limpiar Datos Procesados")
        
        # Obtener el número total de chunks procesados
        stats = self.db.get_document_stats()
        total_chunks = stats.get('total_chunks', 0)
        
        if total_chunks > 0:
            st.warning(f"⚠️ Esto eliminará permanentemente {total_chunks} chunks procesados de todos los documentos.")
            st.info("Los documentos originales se mantendrán, pero deberán ser reprocesados.")
            
            if st.button("🧹 Limpiar todos los chunks procesados", type="primary"):
                try:
                    self.db.clear_processed_chunks()
                    st.success("✅ Todos los chunks procesados han sido eliminados")
                    st.rerun()
                except Exception as e:
                    st.error(f"❌ Error al limpiar datos: {str(e)}")
        else:
            st.info("No hay chunks procesados para limpiar")
