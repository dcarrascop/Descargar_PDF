import streamlit as st
import requests
from bs4 import BeautifulSoup
import zipfile
import io
import re
import pandas as pd

# Función para descargar y procesar PDFs con timeout
def descargar_articulos(articulos, timeout):
    zip_buffer = io.BytesIO()
    log_errores = []  # Lista para guardar los errores

    # Crear un archivo zip
    with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zf:
        progress_bar = st.progress(0)
        total_articulos = len(articulos)

        for i, (titulo, url) in enumerate(articulos):
            try:
                # Mostrar el progreso en el formato requerido
                st.write(f"Procesando {i+1}/{total_articulos} ({int((i+1)/total_articulos*100)}%): {titulo}")
                
                # Descargar la página del artículo
                response = requests.get(url, timeout=timeout)  # Aplicar el timeout
                soup = BeautifulSoup(response.text, 'html.parser')
                pdf_meta = soup.find('meta', attrs={'name': 'citation_pdf_url'})

                if pdf_meta:
                    pdf_url = pdf_meta['content']
                    pdf_response = requests.get(pdf_url, timeout=timeout)  # Aplicar el timeout en la descarga del PDF
                    
                    # Limpiar el nombre del archivo
                    title_clean = re.sub(r'[^\w\s-]', '', titulo).replace(' ', '_')

                    # Agregar el archivo PDF al zip
                    zf.writestr(f"{title_clean}.pdf", pdf_response.content)
                    st.write(f"PDF de {titulo} descargado.")
                else:
                    log_errores.append(f"PDF no encontrado para el artículo: {titulo}, URL: {url}")
                    st.warning(f"Artículo no descargado: {titulo}")  # Cambiar el mensaje al formato deseado

            except requests.exceptions.RequestException as e:
                log_errores.append(f"Error al descargar {titulo}, URL: {url} - {str(e)}")
                st.warning(f"Artículo no descargado: {titulo}")  # Mostrar el mensaje más simple para errores

            # Actualizar la barra de progreso y mostrar el porcentaje
            progress_bar.progress((i + 1) / total_articulos)

        # Crear el archivo de log y añadirlo al zip
        if log_errores:
            log_content = "\n".join(log_errores)
            zf.writestr("00_log_errores.txt", log_content)
            st.write("Log de errores creado y añadido al zip.")

    zip_buffer.seek(0)
    return zip_buffer

# Interfaz de Streamlit
st.title("Descarga de artículos en PDF desde CSV")

# Subir el archivo CSV
uploaded_file = st.file_uploader("Sube tu archivo CSV", type=["csv"])

# Configuración de timeout
timeout = st.number_input("Define el tiempo de timeout en segundos para cada artículo", min_value=1, max_value=180, value=60)

# Variable de estado para almacenar el archivo ZIP
if 'zip_file' not in st.session_state:
    st.session_state.zip_file = None

if uploaded_file:
    # Leer el archivo CSV
    df = pd.read_csv(uploaded_file)

    # Asegurarse de que las columnas 'title' y 'url' existen en tu CSV
    if 'title' in df.columns and 'url' in df.columns:
        # Contar la cantidad de artículos
        total_articulos = len(df)
        st.write(f"Total de artículos: {total_articulos}")

        # Selección de rango de artículos
        start_index = st.number_input("Selecciona el índice de inicio (1 a N)", min_value=1, max_value=total_articulos, value=1)
        end_index = st.number_input("Selecciona el índice de fin (1 a N)", min_value=1, max_value=total_articulos, value=total_articulos)

        # Ajustar el rango al índice 0 basado en Python
        articulos_seleccionados = df[['title', 'url']].iloc[start_index-1:end_index].values.tolist()

        # Botón para iniciar la descarga
        if st.button(f"Descargar artículos {start_index} a {end_index} como ZIP"):
            # Generar el archivo ZIP
            st.session_state.zip_file = descargar_articulos(articulos_seleccionados, timeout)

    else:
        st.error("El archivo CSV debe contener las columnas 'title' y 'url'.")

# Si el archivo ZIP ya fue generado, mostrar el botón de descarga
if st.session_state.zip_file:
    st.download_button(
        label="Descargar archivo ZIP",
        data=st.session_state.zip_file,
        file_name="articulos.zip",
        mime="application/zip"
    )
