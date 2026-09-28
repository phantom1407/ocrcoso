import streamlit as st
import os
import time
import glob
import cv2
import numpy as np
import pytesseract
from PIL import Image
from gtts import gTTS
# Usamos deep-translator para evitar caídas en Streamlit Cloud
from deep_translator import GoogleTranslator

# ---------------------------------------------------------
# ESTILOS CSS PARA EL TEMA AZULITO CLARO
# ---------------------------------------------------------
st.markdown("""
<style>
    /* Fondo principal de la aplicación */
    .stApp {
        background-color: #EBF5FB; /* Azul muy claro / Celeste */
    }
    
    /* Color del texto para títulos y subtítulos */
    h1, h2, h3 {
        color: #21618C !important; /* Azul oscuro elegante */
    }
    
    /* Color de los textos normales */
    p, span, label {
        color: #1B4F72 !important;
    }
    
    /* Estilizar los botones nativos de Streamlit */
    div.stButton > button:first-child {
        background-color: #5DADE2; /* Azul vibrante */
        color: white !important;
        border-radius: 10px;
        border: none;
        font-weight: bold;
    }
    div.stButton > button:first-child:hover {
        background-color: #2874A6; /* Azul más oscuro al pasar el mouse */
        color: white !important;
    }
    
    /* Estilizar los recuadros de subir archivos/cámara */
    .stCamera, .stFileUploader {
        border-radius: 15px;
        border: 2px dashed #5DADE2 !important;
        padding: 10px;
    }
</style>
""", unsafe_allow_html=True)
# ---------------------------------------------------------

# Función de limpieza de audios
def remove_files(n):
    mp3_files = glob.glob("temp/*mp3")
    if len(mp3_files) != 0:
        now = time.time()
        n_days = n * 86400
        for f in mp3_files:
            if os.stat(f).st_mtime < now - n_days:
                os.remove(f)
                print("Deleted ", f)

remove_files(7)

# Interfaz Principal
st.title("🔤 Lector y Traductor de Imágenes")
st.subheader("Extrae texto de tus imágenes y escúchalo en otro idioma 🌊")

# Inicializar variable de texto
text = ""

# --- SECCIÓN DE ENTRADA DE IMAGEN ---
st.markdown("### 📸 1. Sube o toma una foto")
cam_ = st.checkbox("Habilitar Cámara 📷")

if cam_:
    img_file_buffer = st.camera_input("Toma una Foto")
else:
    img_file_buffer = None
    
with st.sidebar:
    st.subheader("⚙️ Opciones de Imagen")
    filtro = st.radio("Aplicar Filtro Invertido (Solo para cámara)", ('No', 'Sí'))

bg_image = st.file_uploader("O carga una imagen desde tus archivos:", type=["png", "jpg", "jpeg"])

st.markdown("---")

# --- PROCESAMIENTO DE IMAGEN ---
if bg_image is not None:
    uploaded_file = bg_image
    st.image(uploaded_file, caption='Imagen cargada.', use_container_width=True)
    
    # Guardar la imagen en el sistema de archivos temporalmente
    with open(uploaded_file.name, 'wb') as f:
        f.write(uploaded_file.read())
    
    st.success(f"¡Imagen leída con éxito!")
    img_cv = cv2.imread(f'{uploaded_file.name}')
    img_rgb = cv2.cvtColor(img_cv, cv2.COLOR_BGR2RGB)
    
    # Extraer texto
    text = pytesseract.image_to_string(img_rgb)
    st.markdown("### 📄 Texto Extraído:")
    st.info(text if text.strip() else "No se detectó texto en la imagen.")

elif img_file_buffer is not None:
    # Leer imagen de la cámara con OpenCV
    bytes_data = img_file_buffer.getvalue()
    cv2_img = cv2.imdecode(np.frombuffer(bytes_data, np.uint8), cv2.IMREAD_COLOR)
    
    # Aplicar el filtro arreglado
    if filtro == 'Sí':
         cv2_img = cv2.bitwise_not(cv2_img)
         
    img_rgb = cv2.cvtColor(cv2_img, cv2.COLOR_BGR2RGB)
    
    # Extraer texto
    text = pytesseract.image_to_string(img_rgb) 
    st.markdown("### 📄 Texto Extraído:")
    st.info(text if text.strip() else "No se detectó texto en la imagen.")


# --- SECCIÓN DE TRADUCCIÓN (BARRA LATERAL) ---
with st.sidebar:
    st.markdown("---")
    st.subheader("🌍 Parámetros de Traducción")
    
    try:
        os.mkdir("temp")
    except:
        pass

    # Diccionario de idiomas para deep-translator
    lang_dict = {
        "Ingles": "en",
        "Español": "es",
        "Bengali": "bn",
        "Coreano": "ko",
        "Mandarin": "zh-CN",
        "Japones": "ja"
    }

    in_lang = st.selectbox("Idioma de entrada", list(lang_dict.keys()))
    out_lang = st.selectbox("Idioma de salida", list(lang_dict.keys()))
    
    input_language = lang_dict[in_lang]
    output_language = lang_dict[out_lang]
      
    english_accent = st.selectbox(
        "Acento de Voz",
        ("Default", "India", "United Kingdom", "United States", "Canada", "Australia", "Ireland", "South Africa"),
    )
      
    if english_accent == "Default": tld = "com"
    elif english_accent == "India": tld = "co.in"
    elif english_accent == "United Kingdom": tld = "co.uk"
    elif english_accent == "United States": tld = "com"
    elif english_accent == "Canada": tld = "ca"
    elif english_accent == "Australia": tld = "com.au"
    elif english_accent == "Ireland": tld = "ie"
    elif english_accent == "South Africa": tld = "co.za"

    display_output_text = st.checkbox("Mostrar texto traducido")

    def text_to_speech_deep(input_lang, output_lang, text_to_translate, tld_code):
        # Traducción con deep-translator
        trans_text = GoogleTranslator(source=input_lang, target=output_lang).translate(text_to_translate)
        
        # Audio con gTTS
        tts = gTTS(trans_text, lang=output_lang, tld=tld_code, slow=False)
        try:
            my_file_name = text_to_translate[0:15].replace(" ", "_").replace("\n", "")
            if not my_file_name:
                my_file_name = "audio"
        except:
            my_file_name = "audio"
            
        tts.save(f"temp/{my_file_name}.mp3")
        return my_file_name, trans_text

    if st.button("🪄 Traducir y Convertir"):
        if text.strip() == "":
            st.warning("¡No hay texto para traducir! Por favor carga una imagen con texto.")
        else:
            with st.spinner("Creando magia azul... 🌊"):
                result_name, output_text = text_to_speech_deep(input_language, output_language, text, tld)
                
                audio_file = open(f"temp/{result_name}.mp3", "rb")
                audio_bytes = audio_file.read()
                
                st.markdown(f"### 🎵 Tu audio:")
                st.audio(audio_bytes, format="audio/mp3", start_time=0)
          
                if display_output_text:
                    st.markdown(f"### 📝 Texto Traducido:")
                    st.success(f"{output_text}")
