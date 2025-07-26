import streamlit as st
import pyttsx3
import os
import base64
import sys
import time 
import speech_recognition as sr
from streamlit_webrtc import webrtc_streamer, AudioProcessorBase, WebRtcMode
import av
import numpy as np
import soundfile as sf

from traductor_kichwa.main import traducir_oracion, normalizar_texto
from PIL import Image
from streamlit.components.v1 import html
from traductor_kichwa.db.consultas import buscar_todas_traducciones

class AudioProcessor(AudioProcessorBase):
    def __init__(self):
        self.frames = []
    def recv(self, frame):
        audio = frame.to_ndarray()
        self.frames.append(audio)
        return frame
    def get_audio(self):
        if self.frames:
            audio_np = np.concatenate(self.frames)
            return audio_np
        return None
    def reset(self):
        self.frames = []

# === FUNCIONES DE AUDIO ===
@st.cache_resource
def get_tts_engine():
    engine = pyttsx3.init()
    engine.setProperty('rate', 100)      # Más lento (valor típico: 100-150)
    engine.setProperty('volume', 0.8)    # Más suave (0.0 a 1.0)
    engine.setProperty('voice', 'spanish')
    return engine

def text_to_audio(text):
    engine = get_tts_engine()
    temp_filename = 'temp_audio.mp3'
    engine.save_to_file(text, temp_filename)
    engine.runAndWait()
    with open(temp_filename, 'rb') as f:
        audio_bytes = f.read()
    os.remove(temp_filename)  # Elimina el archivo temporal
    return audio_bytes

def speech_to_text():
    recognizer = sr.Recognizer()
    mic = sr.Microphone()
    with mic as source:
        # Mensaje con estilo acorde al proyecto
        st.markdown('''
        <div style="background: linear-gradient(135deg, #D4B896, #C9A876); 
                    color: white; padding: 1rem; border-radius: 12px; 
                    margin: 1rem 0; text-align: center; font-weight: 600;">
            🎙️ Grabando... Habla ahora.
        </div>
        ''', unsafe_allow_html=True)
        
        recognizer.adjust_for_ambient_noise(source)
        audio = recognizer.listen(source, timeout=5, phrase_time_limit=10)
        
        try:
            texto = recognizer.recognize_google(audio, language="es-ES")
            
            # Guardar directamente en el cuadro de entrada
            st.session_state["texto_entrada"] = texto
            
            # Traducir automáticamente
            try:
                if len(texto.strip().split()) >= 2:
                    traduccion_auto = traducir_oracion(texto)
                    st.session_state["traduccion"] = traduccion_auto
                else:
                    # Si es una sola palabra, buscar traducciones
                    traducciones = buscar_todas_traducciones(texto.strip())
                    if traducciones:
                        st.session_state["traduccion"] = ", ".join(traducciones)
                    else:
                        st.session_state["traduccion"] = ""
                    
            except Exception as e:
                st.session_state["traduccion"] = ""            
            # Forzar actualización inmediata de la interfaz
            st.rerun()
                
        except sr.UnknownValueError:
            st.markdown('''
            <div style="background: linear-gradient(135deg, #8B7355, #5D4E37); 
                        color: white; padding: 1rem; border-radius: 12px; 
                        margin: 1rem 0; text-align: center; font-weight: 600;">
                ❌ No se pudo entender el audio
            </div>
            ''', unsafe_allow_html=True)
        except sr.RequestError as e:
            st.markdown(f'''
            <div style="background: linear-gradient(135deg, #8B7355, #5D4E37); 
                        color: white; padding: 1rem; border-radius: 12px; 
                        margin: 1rem 0; text-align: center; font-weight: 600;">
                ❌ Error en el servicio de reconocimiento: {e}
            </div>
            ''', unsafe_allow_html=True)
        except Exception as e:
            st.markdown(f'''
            <div style="background: linear-gradient(135deg, #8B7355, #5D4E37); 
                        color: white; padding: 1rem; border-radius: 12px; 
                        margin: 1rem 0; text-align: center; font-weight: 600;">
                ❌ Error inesperado: {str(e)}
            </div>
            ''', unsafe_allow_html=True)

# Función para convertir imagen a base64 con manejo de errores
def get_image_base64(image_path):
    try:
        if os.path.exists(image_path):
            with open(image_path, "rb") as img_file:
                return base64.b64encode(img_file.read()).decode()
    except Exception as e:
        print(f"Error loading image: {e}")
    return None
# Ruta de imágenes
IMGS_PATH = os.path.join(os.path.dirname(__file__), 'traductor_kichwa', 'imagenes')

# ========================================
# 🎯 CONFIGURACIÓN DE IMAGEN DE FONDO
# ========================================
# 👇 CAMBIA AQUÍ el nombre del archivo para la imagen de fondo
IMAGEN_FONDO = 'banner_v5.png'  # 👈 Pon aquí el nombre de tu imagen de fondo

# Configuración de la página
titulo = "TRADUCTOR ESPAÑOL - KICHWA"
st.set_page_config(page_title=titulo, page_icon="🌎", layout="wide")

# Obtener la imagen de fondo en base64 de forma segura
bg_image_path = os.path.join(IMGS_PATH, IMAGEN_FONDO)  # 👈 Usa la variable configurada arriba
bg_image_b64 = get_image_base64(bg_image_path)

# CSS base más seguro
base_css = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Poppins:wght@300;400;500;600;700&display=swap');

:root {
    --bg-primary: #F7F3ED;
    --bg-secondary: #F0E6D6;
    --bg-card: #FFFFFF;
    --accent-primary: #D4B896;
    --accent-secondary: #C9A876;
    --accent-hover: #B8965C;
    --text-primary: #5D4E37;
    --text-secondary: #8B7355;
    --text-muted: #A0926B;
    --border-light: #E8DCC6;
    --shadow-light: rgba(180, 149, 92, 0.15);
    --shadow-medium: rgba(93, 78, 55, 0.1);
}

.stApp {
    background: linear-gradient(135deg, var(--bg-primary) 0%, var(--bg-secondary) 100%);
    font-family: 'Poppins', sans-serif !important;
}
"""

# CSS adicional solo si la imagen existe
background_css = ""
if bg_image_b64:
    background_css = f"""
/* Imagen de fondo con transparencia */
.stApp::before {{
    content: '';
    position: fixed;
    top: 0;
    left: 0;
    width: 100%;
    height: 100%;
    background-image: url('data:image/png;base64,{bg_image_b64}');
    background-size: cover;
    background-position: center;
    background-repeat: no-repeat;
    opacity: 0.2;
    z-index: -1;
    pointer-events: none;
}}
"""

# Aplicar estilos CSS
st.markdown(base_css + background_css + """
.main {
    background: rgba(255, 255, 255, 0.95);
    border-radius: 24px;
    padding: 2.5rem;
    margin: 1rem;
    box-shadow: 0 20px 60px var(--shadow-light);
    backdrop-filter: blur(10px);
    border: 1px solid var(--border-light);
    position: relative;
    z-index: 1;
}

/* Header modernizado */
.modern-header {
    text-align: center;
    margin-bottom: 3rem;
    padding: 2rem 0;
    background: linear-gradient(135deg, var(--accent-primary), var(--accent-secondary));
    border-radius: 20px;
    color: white;
    box-shadow: 0 10px 30px var(--shadow-light);
}

.titulo-principal {
    font-size: 3.2rem;
    font-weight: 700;
    margin-bottom: 0.5rem;
    letter-spacing: -0.5px;
    text-shadow: 2px 2px 4px rgba(0,0,0,0.1);
}

.subtitulo {
    font-size: 1.1rem;
    font-weight: 400;
    opacity: 0.9;
    margin-bottom: 0;
}

/* Animación para las imágenes laterales */
.sidebar-image {
    animation: float 3s ease-in-out infinite;
    transition: transform 0.3s ease;
    border-radius: 15px;
    box-shadow: 0 8px 25px var(--shadow-medium);
    margin-bottom: 1rem;
    overflow: hidden;
}

.sidebar-image:hover {
    transform: scale(1.05) rotate(2deg);
}

@keyframes float {
    0%, 100% {
        transform: translateY(0px);
    }
    50% {
        transform: translateY(-10px);
    }
}

/* Animación alternada para crear efecto de onda */
.sidebar-image:nth-child(even) {
    animation-delay: 1.5s;
}

.sidebar-image:nth-child(3n) {
    animation-delay: 3s;
}

/* Cards modernos */
.instruction-card {
    background: rgba(255, 255, 255, 0.95);
    border-radius: 16px;
    padding: 1.8rem;
    margin-bottom: 2rem;
    box-shadow: 0 8px 25px var(--shadow-medium);
    border-left: 4px solid var(--accent-primary);
    transition: transform 0.3s ease, box-shadow 0.3s ease;
    backdrop-filter: blur(10px);
}

.instruction-card:hover {
    transform: translateY(-2px);
    box-shadow: 0 12px 35px var(--shadow-light);
}

.instruction-title {
    color: var(--text-primary);
    font-size: 1.3rem;
    font-weight: 600;
    margin-bottom: 1rem;
    display: flex;
    align-items: center;
    gap: 0.5rem;
}

.instruction-content {
    color: var(--text-secondary);
    font-size: 1rem;
    line-height: 1.6;
}

/* Input containers modernos */
.input-container {
    background: rgba(255, 255, 255, 0.95);
    border-radius: 20px;
    padding: 2rem;
    margin-bottom: 1.5rem;
    box-shadow: 0 8px 25px var(--shadow-medium);
    border: 1px solid var(--border-light);
    transition: all 0.3s ease;
    backdrop-filter: blur(10px);
}

.input-container:hover {
    box-shadow: 0 12px 35px var(--shadow-light);
    transform: translateY(-1px);
}

.input-label {
    color: var(--text-primary);
    font-size: 1.4rem;
    font-weight: 600;
    text-align: center;
    margin-bottom: 1rem;
    display: block;
}

/* Botones modernos */
.stButton > button {
    background: linear-gradient(135deg, var(--accent-primary), var(--accent-secondary)) !important;
    color: white !important;
    font-weight: 600 !important;
    border: none !important;
    border-radius: 12px !important;
    padding: 0.75rem 1.5rem !important;
    font-size: 0.95rem !important;
    transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1) !important;
    box-shadow: 0 4px 15px var(--shadow-light) !important;
    position: relative !important;
    overflow: hidden !important;
    font-family: 'Poppins', sans-serif !important;
}

.stButton > button:hover {
    background: linear-gradient(135deg, var(--accent-secondary), var(--accent-hover)) !important;
    transform: translateY(-2px) scale(1.02) !important;
    box-shadow: 0 8px 25px var(--shadow-light) !important;
    color: white !important;
}

.stButton > button:active {
    transform: translateY(0) scale(0.98) !important;
    transition: all 0.1s !important;
}

.stButton > button:focus {
    outline: none !important;
    box-shadow: 0 0 0 3px rgba(212, 184, 150, 0.3) !important;
}

/* Text areas modernizadas */
.stTextArea textarea {
    background: var(--bg-primary) !important;
    color: var(--text-primary) !important;
    border: 2px solid var(--border-light) !important;
    border-radius: 12px !important;
    font-size: 1.1rem !important;
    font-family: 'Poppins', sans-serif !important;
    padding: 1rem !important;
    transition: all 0.3s ease !important;
    box-shadow: inset 0 2px 4px rgba(0,0,0,0.05) !important;
}

.stTextArea textarea:focus {
    border-color: var(--accent-primary) !important;
    box-shadow: 0 0 0 3px rgba(212, 184, 150, 0.2), inset 0 2px 4px rgba(0,0,0,0.05) !important;
    outline: none !important;
}

.stTextArea textarea::placeholder {
    color: var(--text-muted) !important;
    opacity: 0.7 !important;
}

.stTextArea textarea:disabled {
    background: var(--bg-secondary) !important;
    color: var(--text-primary) !important;
    opacity: 1 !important;
    border-color: var(--border-light) !important;
}

/* Warnings y alertas */
.stAlert {
    background: linear-gradient(135deg, #FFF8E1, #FFECB3) !important;
    color: var(--text-primary) !important;
    border-left: 4px solid #FFB74D !important;
    border-radius: 8px !important;
    font-family: 'Poppins', sans-serif !important;
}

/* Footer */
.footer {
    text-align: center;
    color: var(--text-secondary);
    font-size: 1rem;
    margin-top: 3rem;
    padding: 2rem;
    background: rgba(240, 230, 214, 0.95);
    border-radius: 16px;
    font-weight: 500;
    backdrop-filter: blur(10px);
}

/* Responsive design */
@media (max-width: 768px) {
    .titulo-principal {
        font-size: 2.5rem;
    }
    
    .main {
        padding: 1.5rem;
        margin: 0.5rem;
    }
    
    .instruction-card {
        padding: 1.2rem;
    }
    
    .input-container {
        padding: 1.5rem;
    }
}

/* Animaciones suaves */
@keyframes fadeInUp {
    from {
        opacity: 0;
        transform: translateY(20px);
    }
    to {
        opacity: 1;
        transform: translateY(0);
    }
}

.fade-in {
    animation: fadeInUp 0.6s ease-out;
}

/* Efecto de pulso para elementos importantes */
@keyframes pulse {
    0%, 100% {
        transform: scale(1);
    }
    50% {
        transform: scale(1.02);
    }
}

.pulse {
    animation: pulse 4s ease-in-out infinite;
}

/* Grid de botones mejorado */
.button-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
    gap: 1rem;
    margin-top: 1.5rem;
}

/* Mejoras para las columnas de Streamlit */
div[data-testid="column"] {
    padding: 0.5rem !important;
}

div[data-testid="stHorizontalBlock"] {
    gap: 1rem !important;
}
</style>
""", unsafe_allow_html=True)

# Layout con imágenes a los costados
col_izq, col_centro, col_der = st.columns([0.8, 6.4, 0.8])

with col_izq:
    # ========================================
    # 🎯 AQUÍ CONFIGURAS LAS IMÁGENES DE LA COLUMNA IZQUIERDA
    # ========================================
    
    # Lista de nombres de archivos de imágenes para la columna izquierda
    imagenes_izquierda = [
        'col_v3.png',    # 👈 CAMBIA AQUÍ: Imagen 1 (arriba)
        'col_v4.png',    # 👈 CAMBIA AQUÍ: Imagen 2
        'col_v3.png',    # 👈 CAMBIA AQUÍ: Imagen 3
        'col_v4.png',    # 👈 CAMBIA AQUÍ: Imagen 4
        'col_v3.png',    # 👈 CAMBIA AQUÍ: Imagen 5
        'col_v4.png'     # 👈 CAMBIA AQUÍ: Imagen 6 (abajo)
    ]
    
    # Mostrar cada imagen de la lista
    for i, nombre_imagen in enumerate(imagenes_izquierda):
        imagen_path = os.path.join(IMGS_PATH, nombre_imagen)
        
        if os.path.exists(imagen_path):
            try:
                img = Image.open(imagen_path)
                # Redimensionar manteniendo la proporción
                img = img.resize((150, 200), Image.Resampling.LANCZOS)
                st.image(img, width=150)
            except Exception as e:
                # Fallback si hay error cargando la imagen específica
                st.markdown(f'''
                <div style="width: 150px; height: 200px; 
                     background: linear-gradient(135deg, var(--accent-primary), var(--accent-secondary)); 
                     border-radius: 15px; margin-bottom: 1rem; opacity: 0.7;
                     display: flex; align-items: center; justify-content: center;
                     color: white; font-weight: bold;">
                    🖼️ {nombre_imagen}
                </div>
                ''', unsafe_allow_html=True)
        else:
            # Si no existe la imagen, mostrar placeholder con el nombre
            st.markdown(f'''
            <div class="sidebar-image" style="width: 150px; height: 200px; 
                 background: linear-gradient(135deg, var(--accent-primary), var(--accent-secondary)); 
                 border-radius: 15px; margin-bottom: 1rem; opacity: 0.7;
                 display: flex; align-items: center; justify-content: center;
                 color: white; font-weight: bold; text-align: center; font-size: 0.8rem;
                 animation-delay: {i * 0.5}s;">
                📁 {nombre_imagen}<br>No encontrada
            </div>
            ''', unsafe_allow_html=True)

with col_centro:
    # Inicializar variables de sesión si no existen
    if "texto_entrada" not in st.session_state:
        st.session_state["texto_entrada"] = ""
    if "traduccion" not in st.session_state:
        st.session_state["traduccion"] = ""
    if "last_input_time" not in st.session_state:
        st.session_state["last_input_time"] = 0
    if "grabando_audio" not in st.session_state:
        st.session_state["grabando_audio"] = False
    if "audio_grabado" not in st.session_state:
        st.session_state["audio_grabado"] = None
    if "auto_transcribiendo" not in st.session_state:
        st.session_state["auto_transcribiendo"] = False

    # Header modernizado
    st.markdown(f'''
    <div class="modern-header fade-in">
        <div class="titulo-principal">{titulo}</div>
        <div class="subtitulo" style="font-size: 1.4rem; font-weight: 500;">Uniendo culturas con innovación / Kawsawallpay takruchishpa yachayta mushukyachinchik</div>
    </div>
    ''', unsafe_allow_html=True)

    # Card de instrucciones modernizada
    st.markdown('''
    <div class="instruction-card fade-in">
        <div class="instruction-title">👨‍🏫 Guía de uso del traductor</div>
        <div class="instruction-content">
            <strong>📝 Estructura recomendada:</strong> Sujeto + Verbo conjugado + Complemento
            <br><br>
            <strong>✅ Elementos importantes:</strong><br>
            • <strong>Pronombres claros:</strong> yo, tú, él, ella, nosotros, ustedes, ellos<br>
            • <strong>Verbo conjugado:</strong> presente, pasado o futuro<br>
            • <strong>Complemento completo:</strong> sin abreviaturas ni errores<br>
            • <strong>Evitar:</strong> expresiones idiomáticas y omisiones
            <br><br>
            <strong>💡 Ejemplos correctos:</strong><br>
            • "yo juego con mis amigos"<br>
            • "tú estudias en la universidad"<br>
            • "él va a comer con su familia"
            <br><br>
            <strong>❌ Errores comunes:</strong><br>
            • "jugamos en la casa" (falta pronombre)<br>
            • "yo jugar casa amigos" (verbo sin conjugar)
        </div>
    </div>
    ''', unsafe_allow_html=True)

    # Container de entrada modernizado
    st.markdown('<div class="input-container fade-in">', unsafe_allow_html=True)
    st.markdown('<div class="input-label">✍️ Ingresa una oracion o palabra a traducir</div>', unsafe_allow_html=True)
    
    texto_entrada = st.text_area(
        label="Área de texto para entrada",
        value=st.session_state["texto_entrada"],
        height=100,
        max_chars=500,
        placeholder="Escribe aquí tu oración o palabra en español...",
        key="texto_entrada_area",
        label_visibility="collapsed"
    )
    
    # Grid de botones modernizado
    st.markdown('<div class="button-grid">', unsafe_allow_html=True)
    col_btn1, col_btn2, col_btn3 = st.columns(3)
    
    with col_btn1:
        btn_traducir = st.button("Traducir Oración", key="btn_traducir", use_container_width=True)
    with col_btn2:
        btn_voz = st.button("Voz a Texto", key="btn_voz", use_container_width=True)
        if btn_voz:
            speech_to_text()
    with col_btn3:
        btn_multi = st.button("Traducir Palabra", key="btn_multi", use_container_width=True)
    
    st.markdown('</div></div>', unsafe_allow_html=True)

    # Lógica de los botones
    if btn_multi:
        palabra = texto_entrada.strip().split()[0] if texto_entrada.strip() else ""
        if not palabra:
            st.warning("Por favor, ingresa una palabra para ver sus traducciones.")
            st.session_state["traduccion"] = ""
        else:
            traducciones = buscar_todas_traducciones(palabra)
            if traducciones:
                st.session_state["traduccion"] = ", ".join(traducciones)
            else:
                st.session_state["traduccion"] = ""
                st.warning("No se encontraron traducciones para esa palabra.")

    if btn_traducir:
        if texto_entrada.strip() == "":
            st.warning("Por favor, ingresa una oración para traducir.")
            st.session_state["traduccion"] = ""
        elif len(texto_entrada.strip().split()) < 2:
            st.warning("La oración debe tener al menos un sujeto y un verbo.")
            st.session_state["traduccion"] = ""
        else:
            st.session_state["last_input_time"] = time.time()
            try:
                traduccion = traducir_oracion(texto_entrada)
                st.session_state["traduccion"] = traduccion
            except Exception as e:
                st.warning(f"Ocurrió un error inesperado: {str(e)}")
                st.session_state["traduccion"] = ""

    # Container de traducción modernizado - SIEMPRE VISIBLE
    traduccion = st.session_state.get("traduccion", "")
    
    st.markdown('<div class="input-container fade-in">', unsafe_allow_html=True)
    st.markdown('<div class="input-label">🌍 Traducción en Kichwa</div>', unsafe_allow_html=True)
    
    # Mostrar placeholder si no hay traducción
    placeholder_text = "La traducción aparecerá aquí..." if not traduccion else ""
    
    st.text_area(
        label="Área de texto para traducción",
        value=traduccion,
        height=100,
        key="traduccion_area",
        disabled=True,
        placeholder=placeholder_text,
        label_visibility="collapsed"
    )
    
    # Botón de audio modernizado
    if traduccion:
        st.markdown('<div class="button-grid">', unsafe_allow_html=True)
        # Botón personalizado con la misma lógica CSS que los otros botones
        audio_button_html = f'''
        <div class="stButton">
            <button onclick="playAudio()" style="width: 100%;">
                Escuchar Pronunciación
            </button>
        </div>
        <script>
        function playAudio() {{
            // Crear elemento de audio y reproducir
            const audio = new Audio('data:audio/mp3;base64,{base64.b64encode(text_to_audio(traduccion)).decode()}');
            audio.play();
        }}
        </script>
        '''
        st.markdown(audio_button_html, unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)
    
    st.markdown('</div>', unsafe_allow_html=True)

    # Auto-refresh lógica
    if st.session_state["texto_entrada"].strip() != "" and time.time() - st.session_state["last_input_time"] <= 3:
        st.rerun()

with col_der:
    # ========================================
    # 🎯 AQUÍ CONFIGURAS LAS IMÁGENES DE LA COLUMNA DERECHA
    # ========================================
    
    # Lista de nombres de archivos de imágenes para la columna derecha
    imagenes_derecha = [
        'col_v1.png',    # 👈 CAMBIA AQUÍ: Imagen 1 (arriba)
        'col_v2.png',    # 👈 CAMBIA AQUÍ: Imagen 2
        'col_v1.png',    # 👈 CAMBIA AQUÍ: Imagen 3
        'col_v2.png',    # 👈 CAMBIA AQUÍ: Imagen 4
        'col_v1.png',    # 👈 CAMBIA AQUÍ: Imagen 5
        'col_v2.png'     # 👈 CAMBIA AQUÍ: Imagen 6 (abajo)
    ]
    
    # Mostrar cada imagen de la lista
    for i, nombre_imagen in enumerate(imagenes_derecha):
        imagen_path = os.path.join(IMGS_PATH, nombre_imagen)
        
        if os.path.exists(imagen_path):
            try:
                img = Image.open(imagen_path)
                # Redimensionar manteniendo la proporción
                img = img.resize((150, 200), Image.Resampling.LANCZOS)
                st.image(img, width=150)
            except Exception as e:
                # Fallback si hay error cargando la imagen específica
                st.markdown(f'''
                <div style="width: 150px; height: 200px; 
                     background: linear-gradient(135deg, var(--accent-primary), var(--accent-secondary)); 
                     border-radius: 15px; margin-bottom: 1rem; opacity: 0.7;
                     display: flex; align-items: center; justify-content: center;
                     color: white; font-weight: bold;">
                    🖼️ {nombre_imagen}
                </div>
                ''', unsafe_allow_html=True)
        else:
            # Si no existe la imagen, mostrar placeholder con el nombre
            st.markdown(f'''
            <div class="sidebar-image" style="width: 150px; height: 200px; 
                 background: linear-gradient(135deg, var(--accent-primary), var(--accent-secondary)); 
                 border-radius: 15px; margin-bottom: 1rem; opacity: 0.7;
                 display: flex; align-items: center; justify-content: center;
                 color: white; font-weight: bold; text-align: center; font-size: 0.8rem;
                 animation-delay: {i * 0.5}s;">
                📁 {nombre_imagen}<br>No encontrada
            </div>
            ''', unsafe_allow_html=True)

# Footer modernizado
st.markdown('''
<div class="footer fade-in">
    🎓 Proyecto estudiantil de Big Data - M4A | 2025<br>
    <small>Desarrollado con ❤️ para preservar la cultura Kichwa</small>
</div>
''', unsafe_allow_html=True)

