import streamlit as st
import requests
from bs4 import BeautifulSoup
import zipfile
import io
import re

# Función para descargar y procesar PDFs
def descargar_articulos(articulos):
    zip_buffer = io.BytesIO()
    log_errores = []  # Lista para guardar los errores

    # Crear un archivo zip
    with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zf:
        for i, (titulo, url) in enumerate(articulos):
            try:
                st.write(f"Procesando {i+1}: {titulo}")
                response = requests.get(url)
                soup = BeautifulSoup(response.text, 'html.parser')
                pdf_meta = soup.find('meta', attrs={'name': 'citation_pdf_url'})

                if pdf_meta:
                    pdf_url = pdf_meta['content']
                    pdf_response = requests.get(pdf_url)
                    
                    # Limpiar el nombre del archivo
                    title_clean = re.sub(r'[^\w\s-]', '', titulo).replace(' ', '_')

                    # Agregar el archivo PDF al zip
                    zf.writestr(f"{title_clean}.pdf", pdf_response.content)
                    st.write(f"PDF de {titulo} descargado.")
                else:
                    log_errores.append(f"PDF no encontrado para el artículo: {titulo}, URL: {url}")

            except requests.exceptions.RequestException as e:
                log_errores.append(f"Error al descargar {titulo}, URL: {url} - {str(e)}")

        # Crear el archivo de log y añadirlo al zip
        if log_errores:
            log_content = "\n".join(log_errores)
            zf.writestr("log_errores.txt", log_content)
            st.write("Log de errores creado y añadido al zip.")

    zip_buffer.seek(0)
    return zip_buffer

# Definir los artículos de prueba
articulos_prueba = [
    ("Artículo 1", "http://www.scielo.org.mx/scielo.php?script=sci_arttext&pid=S2448-878X2024000200279&lang=es"),
    ("Artículo 2", "http://www.scielo.org.mx/scielo.php?script=sci_arttext&pid=S2448-878X2024000200041&lang=es"),
    # Agrega más artículos según sea necesario
]

# Interfaz de Streamlit
st.title("Descarga de artículos en PDF")

# Botón para descargar
if st.button("Descargar PDFs como ZIP"):
    zip_file = descargar_articulos(articulos_prueba)
    st.download_button(
        label="Descargar archivo ZIP",
        data=zip_file,
        file_name="articulos.zip",
        mime="application/zip"
    )
