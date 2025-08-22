import streamlit as st
from streamlit_mic_recorder import speech_to_text
import asyncio
from datetime import datetime
from io import BytesIO
import edge_tts
#from ragS import ask_question
from rag import ask_question


VOICE = "es-MX-DaliaNeural"
DEFAULT_LANGUAGE = "es"


class LlmInterface:
    """Componente UI para interactuar con un modelo LLM y respuestas en audio."""

    def __init__(self, db, vs_manager, embed_model):
        self.db = db
        self.vs_manager = vs_manager
        self.embed_model = embed_model

        # Inicializa el historial de mensajes si aún no existe
        if "messages" not in st.session_state:
            st.session_state.messages = []

    def show_llm_interface(self):
        """Muestra la interfaz de chat (voz y texto) y la respuesta de la IA."""
        st.subheader("💬 Chat con la IA")
        
        # Mostrar historial primero
        self.display_chat_history()
        
        # Crear área de input
        user_input = self.create_input_area()

        # Procesar input si existe
        if user_input:
            self.process_user_input_sync(user_input)
            # Forzar rerun para actualizar la interfaz
            st.rerun()

    def display_chat_history(self):
        """Muestra los mensajes anteriores del chat."""
        for message in st.session_state.messages:
            with st.chat_message(message["role"]):
                st.write(message["content"])
                if message["role"] == "assistant" and "audio" in message:
                    st.audio(message["audio"], format='audio/wav')

    def create_input_area(self):
        """Zona de entrada con micrófono o texto."""
        # Usar contenedor fijo en la parte inferior
        with st.container():
            col1, col2 = st.columns([4, 1])
            
            with col1:
                text_input = st.chat_input("Escribe tu mensaje...")
            
            with col2:
                # Crear key único para evitar conflictos
                voice_key = f"speech_to_text_{len(st.session_state.messages)}"
                voice_input = speech_to_text(
                    language=DEFAULT_LANGUAGE,
                    start_prompt="🎤",
                    stop_prompt="⏹️",
                    just_once=True,
                    use_container_width=True,
                    key=voice_key
                )
        
        return voice_input if voice_input else text_input

    def process_user_input_sync(self, user_input: str):
        """Procesa la entrada del usuario de manera síncrona."""
        # Agregar mensaje del usuario inmediatamente
        self.add_message_sync("user", user_input)
        
        # Mostrar el mensaje del usuario
        with st.chat_message("user"):
            st.write(user_input)
        
        # Mostrar indicador de procesamiento
        with st.chat_message("assistant"):
            with st.spinner("Pensando..."):
                start_time = datetime.now()
                
                # Generar respuesta
                response = ask_question(user_input)
                
                # Generar audio de manera síncrona
                audio_data = self.generate_audio_sync(response)
                
                end_time = datetime.now()
                elapsed = (end_time - start_time).total_seconds()
        
        # Agregar respuesta al historial
        self.add_message_sync("assistant", response, audio_data)
        
        # Mostrar tiempo de respuesta
        st.success(f"🕐 Respondido en {elapsed:.2f} segundos")

    def add_message_sync(self, role: str, content: str, audio_data=None):
        """Agrega mensaje al historial de manera síncrona."""
        message = {"role": role, "content": content}
        
        if audio_data:
            message["audio"] = audio_data
            
        st.session_state.messages.append(message)

    def generate_audio_sync(self, text: str, voice=VOICE, rate="+0%", pitch="+0Hz", volume="+0%"):
        """Genera audio desde texto usando Edge TTS de manera síncrona."""
        try:
            # Usar asyncio.run() solo para la generación de audio
            audio_data = asyncio.run(self._generate_audio_async(text, voice, rate, pitch, volume))
            return audio_data
        except Exception as e:
            st.error(f"Error generando audio: {e}")
            return None

    async def _generate_audio_async(self, text: str, voice=VOICE, rate="+0%", pitch="+0Hz", volume="+0%"):
        """Método auxiliar asíncrono para generar audio."""
        try:
            communicate = edge_tts.Communicate(
                text=text, voice=voice, rate=rate, pitch=pitch, volume=volume
            )

            audio_data = bytearray()
            async for chunk in communicate.stream():
                if chunk["type"] == "audio":
                    audio_data.extend(chunk["data"])

            return bytes(audio_data) if audio_data else None

        except Exception as e:
            return None