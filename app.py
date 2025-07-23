import streamlit as st
import pyttsx3
import os
import base64
import sys
import time 

from traductor_kichwa.main import traducir_oracion, normalizar_texto
from PIL import Image
from streamlit.components.v1 import html
from traductor_kichwa.db.consultas import buscar_todas_traducciones

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

# Ruta de imágenes
IMGS_PATH = os.path.join(os.path.dirname(__file__), 'traductor_kichwa', 'imagenes')

# Configuración de la página
titulo = "TRADUCTOR ESPAÑOL - KICHWA"
st.set_page_config(page_title=titulo, page_icon="🌎", layout="wide")

# Estilos personalizados (solo un bloque de fondo)
st.markdown(
    f"""
    <style>
    .stApp {{
        background: #EBE4D4 !important;
        background-image: url('traductor_kichwa/imagenes/bnner_v4.jpg');
        background-repeat: no-repeat;
        background-position: center 80px;
        background-size: 500px auto;
        background-attachment: fixed;
        font-family: 'Times New Roman', Times, serif !important;
    }}
    .main {{
        background: rgba(255,255,255,0.85);
        border-radius: 22px;
        padding: 2em 1em;
        box-shadow: 0 6px 32px rgba(120,180,220,0.10);
        font-family: 'Times New Roman', Times, serif !important;
    }}
    .titulo-principal {{
        font-size: 2.8em;
        font-weight: bold;
        color: #9E693E;
        text-align: center;
        margin-bottom: 0.5em;
        letter-spacing: 2px;
        text-shadow: 1px 1px 8px #e3f2fd;
        font-family: 'Times New Roman', Times, serif !important;
    }}
    .subtitulo {{
        color: #9E693E;
        text-align: center;
        font-size: 1.2em;
        margin-bottom: 2em;
        font-family: 'Times New Roman', Times, serif !important;
    }}
    .stButton>button {{
        background-color: #B6A886;
        color: #222 !important;
        font-weight: bold;
        border-radius: 12px;
        border: none;
        padding: 0.5em 2em;
        margin-top: 1em;
        transition: 0.3s;
        box-shadow: 0 2px 12px #e3f2fd;
        max-width: 300px;
        width: 100%;
        margin-left: auto;
        margin-right: auto;
        display: block;
    }}
    .stButton>button:active, .stButton>button:focus, .stButton>button:visited {{
        color: #222 !important;
        background-color: #A89B7C;
    }}
    .stButton>button:disabled {{
        color: #222 !important;
        opacity: 0.7;
    }}
    .stButton>button:hover {{
        background-color: #A89B7C;
        color: #fff;
        box-shadow: 0 4px 24px #b6a88699;
        transform: translateY(-2px) scale(1.04);
        transition: all 0.2s cubic-bezier(.4,0,.2,1);
    }}
    .stTextArea textarea {{
        background: #F5F3EC;
        color: #222;
        border-radius: 10px;
        border: 2px solid #B6A886;
        font-size: 1.1em;
        transition: background 0.3s, color 0.3s;
        box-shadow: 0 1px 6px #e3f2fd;
    }}
    .stTextArea textarea:hover {{
        box-shadow: 0 4px 24px #b6a88699;
        border: 2px solid #B6A886;
        transition: all 0.2s cubic-bezier(.4,0,.2,1);
    }}
    .stTextArea textarea:disabled {{
        background: #f5fafd;
        color: #222;
        opacity: 1;
    }}
    .stRadio > div {{
        background: #eaf6fb;
        color: #222;
        border-radius: 10px;
        padding: 0.5em 0.5em;
        margin-bottom: 1em;
        border: 2px solid #b7e5f8;
        transition: background 0.3s, color 0.3s;
    }}
    .stAlert {{
        background: #fffbe7;
        color: #333;
        border-left: 5px solid #ffe082;
    }}
    hr {{
        border: none;
        border-top: 2px solid #b7e5f8;
    }}
    [data-theme="dark"] .stTextArea textarea {{
        background: #23272f !important;
        color: #fff !important;
        border: 2px solid #90caf9 !important;
    }}
    [data-theme="dark"] .stTextArea textarea::placeholder {{
        color: #e0e0e0 !important;
        opacity: 1 !important;
    }}
    [data-theme="dark"] .stTextArea textarea:disabled {{
        background: #18191a !important;
        color: #fff !important;
    }}
    [data-theme="light"] .stTextArea textarea {{
        background: #eaf6fb !important;
        color: #222 !important;
        border: 2px solid #b7e5f8 !important;
    }}
    [data-theme="light"] .stTextArea textarea::placeholder {{
        color: #666 !important;
        opacity: 1 !important;
    }}
    [data-theme="light"] .stTextArea textarea:disabled {{
        background: #f5fafd !important;
        color: #222 !important;
    }}
    .stTextArea, .stTextInput, .stButton {{
        width: 100%;
        max-width: 600px !important;
        margin-left: auto;
        margin-right: auto;
    }}
    </style>
    """,
    unsafe_allow_html=True
)

st.markdown("""
<style>
/* Reduce el gap entre columnas de Streamlit solo para los botones */
div[data-testid="column"] > div {
    padding-right: 0 !important;
    padding-left: 0 !important;
}
div[data-testid="stHorizontalBlock"] {
    gap: 0 !important;
}
/* Personaliza el label del área de texto */
label[data-testid="stMarkdownContainer"] > div, .stTextArea label {
    color: #9E693E !important;
    font-size: 1.18em !important;
    font-weight: bold !important;
}
</style>
""", unsafe_allow_html=True)

# Cambios de estilos para color de texto y tamaño de labels
st.markdown("""
<style>
.stTextArea textarea, .stTextInput input {
    color: #000000 !important;
}
.stTextArea textarea::placeholder {
    color: #000000 !important;
    opacity: 1 !important;
}
label[data-testid="stMarkdownContainer"] > div, .stTextArea label {
    color: #9E693E !important;
    font-size: 1.45em !important;
    font-weight: bold !important;
}
.stTextArea label[for="texto_entrada_area"],
.stTextArea label[for="texto_entrada_area"] > div,
.stTextArea label[for="texto_entrada_area"] * {
    color: #9E693E !important;
    font-size: 3em !important;
    font-weight: bold !important;
    line-height: 1.1 !important;
    text-align: center !important;
    width: 100% !important;
    display: block !important;
    white-space: normal !important;
    word-break: break-word !important;
}
.stTextArea label[for="traduccion_area"] {
    color: #9E693E !important;
    font-size: 1.45em !important;
    font-weight: bold !important;
}
</style>
""", unsafe_allow_html=True)

# Layout con imágenes a los costados
col_izq, col_centro, col_der = st.columns([0.5, 7, 0.5])

with col_izq:
    img_izq1 = Image.open(os.path.join(IMGS_PATH, 'borde_v1.png')).resize((200, 400))
    st.image(img_izq1)
    img_izq2 = Image.open(os.path.join(IMGS_PATH, 'borde_v1.png')).resize((200, 400))
    st.image(img_izq2)
    img_izq2 = Image.open(os.path.join(IMGS_PATH, 'borde_v1.png')).resize((200, 400))
    st.image(img_izq2)
    img_izq2 = Image.open(os.path.join(IMGS_PATH, 'borde_v1.png')).resize((200, 400))
    st.image(img_izq2)
    img_izq2 = Image.open(os.path.join(IMGS_PATH, 'borde_v1.png')).resize((200, 400))
    st.image(img_izq2)
    img_izq2 = Image.open(os.path.join(IMGS_PATH, 'borde_v1.png')).resize((200, 400))


with col_centro:
    # Inicializar variables de sesión si no existen
    if "texto_entrada" not in st.session_state:
        st.session_state["texto_entrada"] = ""
    if "traduccion" not in st.session_state:
        st.session_state["traduccion"] = ""
    if "last_input_time" not in st.session_state:
        st.session_state["last_input_time"] = 0
    # Título centrado
    st.markdown(f'<div class="titulo-principal" style="display:table; margin:0 auto;">{titulo}</div>', unsafe_allow_html=True)
    # Subtítulo
    descripcion = "Uniendo culturas con innovación / Kawsawallpay takruchishpa yachayta mushukyachinchik"
    st.markdown(f'<div class="subtitulo">{descripcion}</div>', unsafe_allow_html=True)
    # Instrucciones de uso del traductor
    st.markdown('''
    <div style="max-width:600px; margin:0 auto;">
      <div style="background: #F5F3EC; border-left: 5px solid #B6A886; padding: 1.2em 1em; border-radius: 12px; margin-bottom: 1.5em; font-size:1.08em;">
      <span style="font-size:1.15em;">👉 <b>Estructura: Sujeto + Verbo conjugado + Complemento</b></span><br>
      <ul style="margin-top:0.7em; margin-bottom:0.7em;">
        <li><b>Pronombres claros:</b> yo, tú, él, ella, nosotros, ustedes, ellos</li>
        <li><b>Verbo:</b> siempre conjugado (presente, pasado o futuro)</li>
        <li><b>Complemento:</b> sin abreviaturas ni errores ortográficos</li>
        <li><b>Evita:</b> expresiones idiomáticas y omitir pronombre o conjugación</li>
      </ul>
      <b>Ejemplos:</b><br>
      • yo juego con mis amigos<br>
      • tú estudias en la universidad<br>
      • él va a comer con su familia<br><br>
      <b>Errores comunes:</b><br>
      • jugamos en la casa (falta pronombre)<br>
      • yo jugar casa amigos (verbo sin conjugar)
      </div>
    </div>
    ''', unsafe_allow_html=True)

    # Cuadro de entrada de texto y botones juntos, usando Streamlit y CSS mejorado
    st.markdown('<div style="max-width:400px; margin:0 auto;">', unsafe_allow_html=True)
    st.markdown(
        '<div style="color:#9E693E; font-size:2em; font-weight:bold; text-align:center; margin-bottom:0.2em;">'
        'Ingresa la oración o palabra a traducir:'
        '</div>',
        unsafe_allow_html=True
    )
    texto_entrada = st.text_area(
        label="",  # Sin label nativo
        value=st.session_state["texto_entrada"],
        height=80,
        max_chars=500,
        placeholder="Escribe aquí tu texto...",
        key="texto_entrada_area"
    )
    col_btn_trad, col_btn_voz, col_btn_multi = st.columns([1, 1, 1], gap="small")
    with col_btn_trad:
        btn_traducir = st.button("🔄 Traducir oracion", key="btn_traducir", use_container_width=True)
    with col_btn_voz:
        btn_voz = st.button("🎤 Escuchar y transcribir voz", key="btn_voz", use_container_width=True)
    with col_btn_multi:
        btn_multi = st.button("🔄 Traducir palabra", key="btn_multi", use_container_width=True)

    if btn_multi:
        palabra = texto_entrada.strip().split()[0] if texto_entrada.strip() else ""
        if not palabra:
            st.markdown('<div style="background:#f5f3ec; color:#9E693E; border-left:5px solid #B6A886; padding:1em 1em; border-radius:10px; margin-bottom:1em; font-size:1.05em;">Por favor, ingresa una palabra para ver sus traducciones.</div>', unsafe_allow_html=True)
            st.session_state["traduccion"] = ""
        else:
            traducciones = buscar_todas_traducciones(palabra)
            if traducciones:
                st.session_state["traduccion"] = ", ".join(traducciones)
            else:
                st.session_state["traduccion"] = ""
                st.markdown('<div style="background:#f5f3ec; color:#9E693E; border-left:5px solid #B6A886; padding:1em 1em; border-radius:10px; margin-bottom:1em; font-size:1.05em;">No se encontraron traducciones para esa palabra.</div>', unsafe_allow_html=True)
    if btn_traducir:
        if texto_entrada.strip() == "":
            st.warning("Por favor, ingresa una oración para traducir.")
        elif len(texto_entrada.strip().split()) < 2:
            st.warning("La oración debe tener al menos un sujeto y un verbo.")
        else:
            st.session_state["last_input_time"] = time.time()
            try:
                traduccion = traducir_oracion(texto_entrada)
                st.session_state["traduccion"] = traduccion
            except Exception as e:
                st.warning(f"Ocurrió un error inesperado: {str(e)}")
                st.session_state["traduccion"] = ""
    st.markdown('</div>', unsafe_allow_html=True)

    # Cuadro de traducción alineado y centrado
    traduccion = st.session_state["traduccion"] if "traduccion" in st.session_state else ""
    st.markdown('<div style="max-width:400px; margin:0 auto;">', unsafe_allow_html=True)
    st.markdown(
        '<div style="color:#9E693E; font-size:2em; font-weight:bold; text-align:center; margin-bottom:0.2em;">'
        'Traducción:'
        '</div>',
        unsafe_allow_html=True
    )
    st.text_area(
        label="",  # Sin label nativo
        value=traduccion,
        height=80,
        key="traduccion_area",
        disabled=True,
    )
    st.markdown(
        '<style>'
        '.stTextArea textarea#traduccion_area { color: #000000 !important; }'
        '.stTextArea textarea[disabled], .stTextArea textarea:disabled {'
        'color: #000000 !important;'
        'opacity: 1 !important;'
        '-webkit-text-fill-color: #000000 !important;'
        '}'
        '</style>',
        unsafe_allow_html=True
    )
    st.markdown('</div>', unsafe_allow_html=True)


    # Refrescar la app automáticamente si está esperando traducir
    if st.session_state["texto_entrada"].strip() != "" and time.time() - st.session_state["last_input_time"] <= 3:
        st.rerun()

    # Botón para escuchar la traducción (ahora justo debajo del cuadro de traducción)
    if traduccion:
        if st.button("🔊 Escuchar traducción"):
            audio_bytes = text_to_audio(traduccion)
            audio_b64 = base64.b64encode(audio_bytes).decode()
            audio_html = f'''
                <audio src="data:audio/mp3;base64,{audio_b64}" autoplay style="display:none;"></audio>
            '''
            st.markdown(audio_html, unsafe_allow_html=True)

with col_der:
    img_izq2 = Image.open(os.path.join(IMGS_PATH, 'borde_v1.png')).resize((200, 400))
    st.image(img_izq2)
    img_izq2 = Image.open(os.path.join(IMGS_PATH, 'borde_v1.png')).resize((200, 400))
    st.image(img_izq2)
    img_izq2 = Image.open(os.path.join(IMGS_PATH, 'borde_v1.png')).resize((200, 400))
    st.image(img_izq2)
    img_izq2 = Image.open(os.path.join(IMGS_PATH, 'borde_v1.png')).resize((200, 400))
    st.image(img_izq2)
    img_izq2 = Image.open(os.path.join(IMGS_PATH, 'borde_v1.png')).resize((200, 400))
    st.image(img_izq2)



# Pie de página centrado
st.markdown('<div style="display: flex; flex-direction: column; align-items: center; justify-content: center; margin-top: 2em;">', unsafe_allow_html=True)
st.markdown("<div style='text-align:center; color:#000000; font-size:1.1em; margin-top:10px;'>Proyecto estudiantil de big data - M4A | 2025</div>", unsafe_allow_html=True)
st.markdown('</div>', unsafe_allow_html=True)