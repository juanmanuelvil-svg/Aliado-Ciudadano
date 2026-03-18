import streamlit as st
import google.generativeai as genai
from docx import Document
from docx.shared import Pt
from docx.enum.text import WD_ALIGN_PARAGRAPH
from io import BytesIO
import tempfile
import os
from gtts import gTTS
import base64
import urllib.parse

# --- CONFIGURACIÓN DE LA PÁGINA ---
st.set_page_config(page_title="Aliado Ciudadano", page_icon="🤝", layout="centered", initial_sidebar_state="collapsed")

# --- SEGURIDAD Y LLAVE API ---
try:
    api_key = st.secrets["GEMINI_API_KEY"]
    genai.configure(api_key=api_key)
except KeyError:
    st.error("⚠️ Falta configurar la Llave API en los Secrets.")
    st.stop()

# --- FUNCIONES GLOBALES (Word y Voz) ---
def crear_word(texto_oficio):
    doc = Document()
    estilo = doc.styles['Normal']
    estilo.font.name = 'Arial'
    estilo.font.size = Pt(12)
    for linea in texto_oficio.split('\n'):
        if linea.strip():
            p = doc.add_paragraph(linea.strip())
            p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    archivo_memoria = BytesIO()
    doc.save(archivo_memoria)
    return archivo_memoria.getvalue()

def reproducir_audio(texto):
    try:
        tts = gTTS(text=texto, lang='es', slow=False)
        with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as fp:
            tts.save(fp.name)
            with open(fp.name, "rb") as f:
                data = f.read()
                b64 = base64.b64encode(data).decode()
                md = f"""
                    <audio autoplay="true">
                    <source src="data:audio/mp3;base64,{b64}" type="audio/mp3">
                    </audio>
                    """
                st.markdown(md, unsafe_allow_html=True)
            os.remove(fp.name)
    except Exception as e:
        st.error(f"Error reproduciendo audio: {e}")

# --- CABECERA PRINCIPAL ---
st.markdown("<h1 style='text-align: center; color: #0d6efd;'>🤝 ALIADO CIUDADANO</h1>", unsafe_allow_html=True)
st.markdown("<h5 style='text-align: center; color: #495057;'>Tu Gestor y Acompañante Legal</h5>", unsafe_allow_html=True)
st.divider()

# --- CREACIÓN DE PESTAÑAS (TABS) ---
tab_formulario, tab_kiosco = st.tabs(["📝 MODO FORMULARIO (Escrito)", "🗣️ MODO VOZ (Dictado)"])

# =====================================================================
# PESTAÑA 1: MODO FORMULARIO (ESCRITO Y DICTADO)
# =====================================================================
with tab_formulario:
    st.info("💡 **JUSTICIA INCLUSIVA:** Si hablas Español, Náhuatl, Maya, Tseltal, Tsotsil, Mixteco o Zapoteco, graba tu voz aquí. La IA activará tus derechos lingüísticos y exigirá intérprete gratuito.")
    
    st.subheader("Paso 1: Datos del Ciudadano")
    col1, col2 = st.columns(2)
    with col1:
        nombre_p = st.text_input("👤 Nombre Completo:", key="nom_p")
    with col2:
        contacto_p = st.text_input("📍 Domicilio/Teléfono:", key="con_p")

    dep_final_p = st.text_input("🏢 Autoridad Destinataria (Dejar en blanco si no se sabe):", key="dep_p")
    if not dep_final_p: dep_final_p = "Autoridad Competente"

    st.subheader("Paso 2: Tipo de Trámite")
    tipo_tramite_p = st.selectbox("Selecciona una opción:", [
        "📝 Hacer una Petición (Queja de calle, bache, luz, agua)",
        "❓ Pedir Información Pública (Transparencia)",
        "🛡️ Defender mis derechos (Multa, cobro excesivo)",
        "🏥 Solicitar un Servicio (Atención médica, beca)"
    ], key="tram_p")

    st.subheader("Paso 3: Hechos y Evidencia")
    historia_texto_p = st.text_area("⌨️ Describe el problema detalladamente:", height=100, key="hist_p")
    audio_grabado_p = st.audio_input("🎤 O si prefieres, díctalo aquí (Voz):", key="audio_p")
    
    # MEJORA 1: Carga múltiple de archivos (fotos de libretas o más notas de voz)
    archivos_evidencia_p = st.file_uploader("Sube fotos de evidencia o más audios (Opcional, puedes subir varios):", 
                                          type=['png', 'jpg', 'jpeg', 'pdf', 'mp3', 'wav', 'm4a'], 
                                          accept_multiple_files=True, key="evid_p")

    if st.button("✨ REDACTAR DEFENSA LEGAL", use_container_width=True, type="primary", key="btn_prof"):
        if not nombre_p or (not historia_texto_p and not audio_grabado_p and not archivos_evidencia_p):
            st.warning("⚠️ Faltan datos: Nombre y Descripción (escrita, por voz o foto) son obligatorios.")
        else:
            with st.status("⚙️ Procesando el caso legal...", expanded=True) as status_p:
                archivos_temporales_p = []
                try:
                    # Usamos el modelo estable sin parámetros problemáticos
                    model = genai.GenerativeModel('gemini-2.5-flash')
                    
                    status_p.update(label="⏳ Paso 1/2: Analizando evidencias y redactando borrador...", state="running")
                    contenido_prompt_p = []
                    
                    # MEJORA 2 Y 3: Prompt con reglas estrictas de Fecha y Lengua
                    prompt_borrador_p = f"""
                    Actúas como un asistente legal experto en México. 
                    Nombre: {nombre_p} | Contacto: {contacto_p} | Autoridad: {dep_final_p} | Trámite: {tipo_tramite_p}
                    Hechos: {historia_texto_p}
                    
                    INSTRUCCIONES ESTRICTAS:
                    1. FECHA Y LUGAR: El documento DEBE iniciar en la esquina superior derecha con Lugar y Fecha actual (Ej. Municipio, Estado, a [Día] de [Mes] de [Año]). NUNCA pongas la fecha al final.
                    2. REDACCIÓN: En PRIMERA PERSONA ("yo, comparezco").
                    3. LENGUA INDÍGENA: Si detectas lengua indígena en audios o textos, CITA el Art. 2 Constitucional y EXIGE explícitamente la asistencia gratuita de un INTÉRPRETE oficial.
                    4. EVIDENCIAS: Analiza el contenido de todas las fotos o audios adjuntos e intégralos a los hechos.
                    5. FIRMA: Al final solo debe ir "Atentamente" y ({nombre_p}). NUNCA firmes como "Abogado".
                    """
                    
                    if audio_grabado_p:
                        with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as t:
                            t.write(audio_grabado_p.getvalue())
                            archivos_temporales_p.append(t.name)
                            audio_ia_p = genai.upload_file(t.name)
                            contenido_prompt_p.append(audio_ia_p)

                    # Procesamiento múltiple de archivos
                    if archivos_evidencia_p:
                        for archivo in archivos_evidencia_p:
                            ext = f".{archivo.name.split('.')[-1]}"
                            with tempfile.NamedTemporaryFile(delete=False, suffix=ext) as t:
                                t.write(archivo.getvalue())
                                archivos_temporales_p.append(t.name)
                                evid_ia_p = genai.upload_file(t.name)
                                contenido_prompt_p.append(evid_ia_p)

                    contenido_prompt_p.append(prompt_borrador_p)
                    respuesta_borrador_p = model.generate_content(contenido_prompt_p).text
                    
                    # PASO 2: REVISIÓN
                    status_p.update(label="🔍 Paso 2/2: Verificando fundamentos legales...", state="running")
                    prompt_revision_p = f"""
                    Actúas como filtro. Tu ÚNICA tarea es devolver el borrador corregido:
                    1. Eliminar leyes inventadas.
                    2. Eliminar cualquier firma de abogado o cédula.
                    3. Asegurar que la fecha esté al inicio y no al final.
                    DEVUELVE SOLO EL TEXTO DEL OFICIO LEGAL PURO. NO ESCRIBAS NADA MÁS.
                    
                    BORRADOR A LIMPIAR: 
                    {respuesta_borrador_p}
                    """
                    respuesta_final_p = model.generate_content(prompt_revision_p).text.replace("**", "").replace("*", "").replace("#", "")
                    
                    st.session_state['oficio_p'] = respuesta_final_p
                    status_p.update(label="✅ ¡Documento verificado!", state="complete", expanded=False)
                except Exception as e:
                    status_p.update(label="❌ Error.", state="error")
                    st.error(f"Detalle: {e}")
                finally:
                    for ruta in archivos_temporales_p:
                        if os.path.exists(ruta): os.remove(ruta)

    # RESULTADO PROFESIONAL
    if 'oficio_p' in st.session_state:
        st.success("✅ ¡Documento Generado!")
        st.text_area("Vista Previa:", value=st.session_state['oficio_p'], height=350, key="vista_p")
        
        col_w_p, col_wh_p = st.columns(2)
        with col_w_p:
            st.download_button("💾 DESCARGAR EN WORD", data=crear_word(st.session_state['oficio_p']), file_name=f"Oficio_{nombre_p.replace(' ', '_')}.docx", type="primary", use_container_width=True, key="dw_p")
        with col_wh_p:
            msg_p = urllib.parse.quote(f"Hola, necesito ayuda para imprimir este documento oficial:\n\n{st.session_state['oficio_p']}")
            st.link_button("📲 ENVIAR POR WHATSAPP", url=f"https://api.whatsapp.com/send?text={msg_p}", use_container_width=True)

        if st.button("🗑️ LIMPIAR TODO", use_container_width=True, key="limpiar_p"):
            for key in ['oficio_p']: 
                if key in st.session_state: del st.session_state[key]
            st.rerun()

# =====================================================================
# PESTAÑA 2: MODO VOZ (DICTADO PURO / KIOSCO)
# =====================================================================
with tab_kiosco:
    st.markdown("""
        <style>
        div[data-testid="stTabs"] button p {font-size: 18px; font-weight: bold;}
        div.stButton > button:first-child { height: 80px; font-size: 20px; border-radius: 12px; }
        </style>
    """, unsafe_allow_html=True)

    st.info("💡 **JUSTICIA INCLUSIVA:** Si hablas Español, Náhuatl, Maya, Tseltal, Tsotsil, Mixteco o Zapoteco, graba tu voz aquí. La IA activará tus derechos lingüísticos y exigirá intérprete gratuito.")

    if st.button("🆘 NECESITO AYUDA HUMANA", type="primary", use_container_width=True, key="ayuda_k"):
        st.error("🚨 **ALERTA VISUAL:** POR FAVOR, UN ASESOR ACÉRQUESE A AYUDAR AL CIUDADANO.")
    
    st.markdown("### 1️⃣ ¿De qué se trata su problema? Toca un dibujo:")
    if 'categoria_k' not in st.session_state: st.session_state['categoria_k'] = "General"

    col_k1, col_k2 = st.columns(2)
    with col_k1:
        if st.button("💧 Luz, Agua, Calles", use_container_width=True): st.session_state['categoria_k'] = "Servicios Públicos"
        if st.button("🏥 Salud y Médicos", use_container_width=True): st.session_state['categoria_k'] = "Atención Médica"
    with col_k2:
        if st.button("🚓 Multas y Policía", use_container_width=True): st.session_state['categoria_k'] = "Seguridad y Multas"
        if st.button("🌾 Apoyo y Gobierno", use_container_width=True): st.session_state['categoria_k'] = "Programas Sociales"
    
    st.success(f"✅ Tema seleccionado: **{st.session_state['categoria_k']}**")

    st.markdown("### 2️⃣ Toca el micrófono. Dinos tu Nombre y cuál es el problema:")
    audio_grabado_k = st.audio_input("🎤 TOCA AQUÍ PARA HABLAR", key="audio_k")

    st.markdown("### 3️⃣ Sube fotos de evidencia o escritos a mano (Opcional):")
    # Carga múltiple activada aquí también
    archivos_evidencia_k = st.file_uploader("Sube imágenes o audios adicionales:", 
                                          type=['png', 'jpg', 'jpeg', 'pdf', 'mp3', 'wav'], 
                                          accept_multiple_files=True, key="evid_k")

    if audio_grabado_k:
        if st.button("🚀 HACER MI DOCUMENTO", use_container_width=True, type="primary", key="btn_k"):
            with st.status("⚙️ Escuchando y procesando tu voz...", expanded=True) as status_k:
                archivos_temporales_k = []
                try:
                    # Usando modelo estable
                    model = genai.GenerativeModel('gemini-2.5-flash')
                    
                    status_k.update(label="⏳ Paso 1/2: Analizando audio e imágenes...", state="running")
                    
                    # Prompt Kiosco Mejorado
                    prompt_k = f"""
                    Actúas como un asistente legal experto en México. Audio sobre: {st.session_state['categoria_k']}.
                    Genera tu respuesta separada EXACTAMENTE por la palabra "DIVISOR_K".
                    
                    PARTE 1: Un resumen hablado amable en español simple ("Hola, ya terminé tu documento...").
                    DIVISOR_K
                    PARTE 2: El oficio legal completo.
                    
                    INSTRUCCIONES ESTRICTAS PARA LA PARTE 2:
                    1. FECHA: Inicia en la esquina superior derecha con Lugar y Fecha. NUNCA al final.
                    2. REDACCIÓN: PRIMERA PERSONA ("yo, comparezco").
                    3. LENGUAS INDÍGENAS: Si detectas lengua indígena, cita el Art. 2 Constitucional y exige INTÉRPRETE GRATUITO.
                    4. FIRMA: Termina solo con el nombre del ciudadano. NO firmes como "Abogado Pro Bono".
                    """
                    
                    contenido_prompt_k = []
                    
                    with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as t:
                        t.write(audio_grabado_k.getvalue())
                        archivos_temporales_k.append(t.name)
                        audio_ia_k = genai.upload_file(t.name)
                        contenido_prompt_k.append(audio_ia_k)

                    if archivos_evidencia_k:
                        for archivo in archivos_evidencia_k:
                            ext = f".{archivo.name.split('.')[-1]}"
                            with tempfile.NamedTemporaryFile(delete=False, suffix=ext) as t:
                                t.write(archivo.getvalue())
                                archivos_temporales_k.append(t.name)
                                evid_ia_k = genai.upload_file(t.name)
                                contenido_prompt_k.append(evid_ia_k)

                    contenido_prompt_k.append(prompt_k)
                    
                    respuesta_borrador_k = model.generate_content(contenido_prompt_k).text
                    partes = respuesta_borrador_k.split("DIVISOR_K")
                    
                    if len(partes) == 2:
                        resumen_hablado_k = partes[0].replace("*", "").strip()
                        oficio_borrador_k = partes[1].replace("*", "").replace("#", "").strip()
                        
                        # PASO 2: REVISIÓN KIOSCO
                        status_k.update(label="🔍 Paso 2/2: Verificando leyes...", state="running")
                        prompt_revision_k = f"""
                        Filtro de texto automatizado. Devuelve el borrador corregido:
                        1. Asegura que la fecha esté al inicio.
                        2. ELIMINA cualquier firma de abogado o solicitud de cédula.
                        DEVUELVE SOLO EL TEXTO DEL OFICIO LEGAL PURO.
                        
                        BORRADOR: {oficio_borrador_k}
                        """
                        oficio_revisado_k = model.generate_content(prompt_revision_k).text.replace("**", "").replace("*", "").replace("#", "")
                        
                        st.session_state['oficio_k'] = oficio_revisado_k
                        st.session_state['resumen_k'] = resumen_hablado_k
                        status_k.update(label="✅ ¡Documento listo!", state="complete", expanded=False)
                    else:
                        st.error("Error al procesar. Intente de nuevo.")
                except Exception as e:
                    status_k.update(label="❌ Error.", state="error")
                    st.error(f"Detalle: {e}")
                finally:
                    for ruta in archivos_temporales_k:
                        if os.path.exists(ruta): os.remove(ruta)
            
            if 'oficio_k' in st.session_state: st.rerun()

    # RESULTADO KIOSCO
    if 'oficio_k' in st.session_state:
        st.success("✅ ¡DOCUMENTO LISTO!")
        reproducir_audio(st.session_state['resumen_k'])
        st.info(f"🔊 La computadora dice: *{st.session_state['resumen_k']}*")
        
        col_dw_k, col_wpp_k = st.columns(2)
        with col_dw_k:
            st.download_button("🖨️ DESCARGAR EN WORD", data=crear_word(st.session_state['oficio_k']), file_name="Oficio_Dictado.docx", type="primary", use_container_width=True, key="dw_k")
        with col_wpp_k:
            msg_k = urllib.parse.quote(f"Hola, necesito ayuda para imprimir este documento oficial:\n\n{st.session_state['oficio_k']}")
            st.link_button("📲 ENVIAR POR WHATSAPP", url=f"https://api.whatsapp.com/send?text={msg_k}", use_container_width=True)
        
        with st.expander("👀 Ver el documento escrito"):
            st.text_area("Oficio:", value=st.session_state['oficio_k'], height=300, key="vista_k_aliado")

        if st.button("🗑️ EMPEZAR DE NUEVO", use_container_width=True, key="reset_k"):
            for key in ['oficio_k', 'resumen_k', 'categoria_k']: 
                if key in st.session_state: del st.session_state[key]
            st.rerun()

# --- 7. AVISOS LEGALES Y DE PRIVACIDAD GLOBALES ---
st.write("---")
st.markdown("<h5 style='text-align: center; color: #6c757d;'>Información Legal y Transparencia</h5>", unsafe_allow_html=True)

with st.expander("⚖️ AVISO LEGAL Y LÍMITES DE RESPONSABILIDAD (LEER ANTES DE USAR)"):
    st.markdown("""
    **1. No es Asesoría Legal Humana:** "Aliado Ciudadano" es una herramienta tecnológica experimental impulsada por Inteligencia Artificial (IA). No sustituye el consejo, la representación, ni la revisión de un abogado titulado con Cédula Profesional.
    
    **2. Limitaciones de la Tecnología:** La Inteligencia Artificial puede cometer errores, citar artículos derogados, o interpretar incorrectamente el contexto o la traducción de lenguas originarias (alucinaciones de IA).
    
    **3. Responsabilidad del Usuario:** El documento generado es un "borrador" o "formato sugerido". Es responsabilidad absoluta y exclusiva del usuario o del asesor que lo acompaña leer, verificar, corregir y validar el contenido, los fundamentos legales y sus datos personales antes de firmarlo o presentarlo ante cualquier autoridad.
    
    **4. Deslinde de Responsabilidad:** El creador de este software y la plataforma de alojamiento no asumen ninguna responsabilidad legal, civil, penal o administrativa por el resultado de los trámites, rechazos de autoridades, daños, o perjuicios derivados del uso de los textos generados por este sistema.
    """)

with st.expander("🔒 AVISO DE PRIVACIDAD SIMPLIFICADO"):
    st.markdown("""
    De conformidad con la Ley Federal de Protección de Datos Personales en Posesión de los Particulares (LFPDPPP), se informa lo siguiente:
    
    **1. Identidad del Responsable:** El proyecto independiente "Aliado Ciudadano" (desarrollado por Juan Manuel Villegas) es el responsable del tratamiento temporal de los datos recabados en este sitio.
    
    **2. Datos Recabados y Finalidad:** Los datos proporcionados mediante texto, voz (audio) o fotografías (evidencias) se utilizarán **exclusivamente** para redactar y estructurar el documento legal solicitado en tiempo real.
    
    **3. Almacenamiento y Borrado:** Esta plataforma NO almacena sus datos en bases de datos permanentes. La información, audios y evidencias existen únicamente durante su sesión activa (memoria caché) y se eliminan irreversiblemente al presionar el botón de limpiar o al cerrar el navegador.
    
    **4. Transferencia de Datos:** Para poder funcionar, los datos se procesan de manera cifrada a través de las interfaces de programación (APIs) de Google y Streamlit. Al usar esta plataforma, usted consiente este procesamiento automatizado de terceros para la generación de su documento.
    """)

st.caption("© 2026 Aliado Ciudadano v1.0 | Desarrollado para el Acceso a la Justicia Social en México.")
