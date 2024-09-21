pip install streamlit beautifulsoup4 requests

import streamlit as st
import requests
from bs4 import BeautifulSoup
import re
import zipfile
import os
import time
import pandas as pd

# Título de la aplicación
st.title("Descarga de PDFs desde URLs de artículos académicos")

# Paso 1: Subir el archivo CSV
st.header("Subir archivo CSV")
uploaded_file = st.file_uploader("Selecciona el archivo CSV", type="csv")

if uploaded_file is not None:
    # Paso 2: Leer el archivo CSV subido
    st.write("Archivo CSV cargado exitosamente.")
    csv_data = pd.read_csv(uploaded_file)
    
    # Mostrar una vista previa del archivo
    st.write("Vista previa del archivo CSV:")
    st.dataframe(csv_data.head())

    # Paso 3: Iniciar la descarga de PDFs
    if st.button("Iniciar descarga de PDFs"):
        # Especificar la ruta para guardar el archivo ZIP
        zip_filename = "articulos_pdf.zip"
        log_filename = "articulos_fallidos.log"
        
        # Crear archivo de log
        with open(log_filename, 'w', encoding='utf-8') as log_file:
            log_file.write('Artículos con problemas en la descarga o sin PDF encontrado:\n\n')

        # Crear archivo ZIP
        with zipfile.ZipFile(zip_filename, 'w') as zipf:
            for index, row in csv_data.iterrows():
                # Obtener el título y la URL
                title = row['title'].strip()
                article_url = row['url'].strip()
                
                # Limpiar el título para usarlo como nombre de archivo
                title_clean = re.sub(r'[^\w\s-]', '', title)
                title_clean = re.sub(r'\s+', '_', title_clean)

                st.write(f"Procesando artículo {index + 1}: {title}")
                st.write(f"URL del artículo: {article_url}")

                try:
                    # Obtener el contenido HTML del artículo
                    response = requests.get(article_url, timeout=20)
                    soup = BeautifulSoup(response.text, 'html.parser')

                    # Buscar el enlace al PDF
                    pdf_meta = soup.find('meta', attrs={'name': 'citation_pdf_url'})

                    if pdf_meta:
                        pdf_url = pdf_meta['content']
                        st.write(f"Enlace al PDF encontrado: {pdf_url}")

                        # Descargar el PDF en memoria
                        pdf_response = requests.get(pdf_url, timeout=20)
                        pdf_data = pdf_response.content

                        # Crear un nombre temporal para el archivo
                        pdf_filename = f"{title_clean}.pdf"

                        # Guardar temporalmente el archivo PDF
                        with open(pdf_filename, 'wb') as temp_pdf_file:
                            temp_pdf_file.write(pdf_data)

                        # Agregar el archivo PDF al ZIP
                        zipf.write(pdf_filename, os.path.basename(pdf_filename))

                        # Eliminar el archivo temporal
                        os.remove(pdf_filename)

                        st.write(f"PDF descargado y agregado al ZIP como: {pdf_filename}")
                    else:
                        st.write(f"No se encontró enlace PDF en: {article_url}")
                        with open(log_filename, 'a', encoding='utf-8') as log_file:
                            log_file.write(f"Título: {title} - No se encontró enlace PDF.\n")

                except requests.exceptions.Timeout:
                    st.write(f"Tiempo de espera excedido para el artículo: {title}")
                    with open(log_filename, 'a', encoding='utf-8') as log_file:
                        log_file.write(f"Título: {title} - Timeout al descargar el PDF.\n")

                except requests.exceptions.RequestException as e:
                    st.write(f"Ocurrió un error al intentar descargar el PDF del artículo: {title}. Error: {e}")
                    with open(log_filename, 'a', encoding='utf-8') as log_file:
                        log_file.write(f"Título: {title} - Error: {e}\n")

                # Pausa entre descargas
                time.sleep(2)

        # Mostrar enlace para descargar el archivo ZIP
        with open(zip_filename, 'rb') as zipf:
            st.download_button(
                label="Descargar archivo ZIP con PDFs",
                data=zipf,
                file_name=zip_filename,
                mime='application/zip'
            )

        # Mostrar el archivo de log de errores
        with open(log_filename, 'r', encoding='utf-8') as logf:
            log_content = logf.read()
            st.write("Log de errores:")
            st.text(log_content)
