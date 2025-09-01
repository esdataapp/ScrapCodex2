import os
import time
import glob
import re
from datetime import datetime
from typing import Dict

import pandas as pd
from bs4 import BeautifulSoup
from seleniumbase import Driver
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

# --- Configuración ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(os.path.dirname(BASE_DIR), 'data')

def scrape_property_detail_complete(driver, html):
    """Extrae TODOS los campos como el script original"""
    soup = BeautifulSoup(html, "html.parser")
    data = {}

    # 1. Tipo de inmueble, área, recámaras y estacionamientos
    h2 = soup.find("h2", class_="title-type-sup-property")
    if h2:
        tokens = [t.strip() for t in h2.get_text(separator="·").split("·") if t.strip()]

        data["tipo_propiedad"] = tokens[0] if len(tokens) > 0 else ""
        print("tipo_propiedad:", data["tipo_propiedad"])
        time.sleep(0.05)

        data["area_m2"] = tokens[1] if len(tokens) > 1 else ""
        print("area_m2:", data["area_m2"])
        time.sleep(0.05)

        if len(tokens) > 2:
            match = re.search(r"(\d+)", tokens[2])
            data["recamaras"] = match.group(1) if match else ""
        else:
            data["recamaras"] = ""
        print("recamaras:", data["recamaras"])
        time.sleep(0.05)

        if len(tokens) > 3:
            match = re.search(r"(\d+)", tokens[3])
            data["estacionamientos"] = match.group(1) if match else ""
        else:
            data["estacionamientos"] = ""
        print("estacionamientos:", data["estacionamientos"])
        time.sleep(0.05)
    else:
        data["tipo_propiedad"] = data["area_m2"] = data["recamaras"] = data["estacionamientos"] = ""
        print("tipo_propiedad:", data["tipo_propiedad"])
        print("area_m2:", data["area_m2"])
        print("recamaras:", data["recamaras"])
        print("estacionamientos:", data["estacionamientos"])
        time.sleep(0.05)

    # 2. Operación, precio y mantenimiento
    price_container = soup.find("div", class_="price-container-property")
    if price_container:
        price_value_div = price_container.find("div", class_="price-value")
        if price_value_div:
            text = price_value_div.get_text(" ", strip=True)
            if "venta" in text.lower():
                data["operacion"] = "venta"
            elif "renta" in text.lower():
                data["operacion"] = "renta"
            else:
                data["operacion"] = ""
            print("operacion:", data["operacion"])
            time.sleep(0.05)

            span_precio = price_value_div.find("span")
            data["precio"] = span_precio.get_text(strip=True) if span_precio else ""
            print("precio:", data["precio"])
            time.sleep(0.05)
        else:
            data["operacion"] = data["precio"] = ""
            print("operacion:", data["operacion"])
            print("precio:", data["precio"])
            time.sleep(0.05)

        extra_div = price_container.find("div", class_="price-extra")
        if extra_div:
            span_mant = extra_div.find("span", class_="price-expenses")
            data["mantenimiento"] = span_mant.get_text(strip=True) if span_mant else ""
        else:
            data["mantenimiento"] = ""
        print("mantenimiento:", data["mantenimiento"])
        time.sleep(0.05)
    else:
        data["operacion"] = data["precio"] = data["mantenimiento"] = ""
        print("operacion:", data["operacion"])
        print("precio:", data["precio"])
        print("mantenimiento:", data["mantenimiento"])
        time.sleep(0.05)

    # 3. Dirección
    location_div = soup.find("div", class_="section-location-property")
    if location_div:
        h4 = location_div.find("h4")
        data["direccion"] = h4.get_text(strip=True) if h4 else ""
    else:
        data["direccion"] = ""
    print("direccion:", data["direccion"])
    time.sleep(0.05)

    # Extraer la URL del mapa estático
    map_container = soup.find("div", class_="static-map-container")
    if map_container:
        img = map_container.find("img", id="static-map")
        if img:
            url = img.get("src", "")
            if url.startswith("//"):
                url = "https:" + url
            data["ubicacion_url"] = url
        else:
            data["ubicacion_url"] = ""
    else:
        data["ubicacion_url"] = ""
    print("ubicacion_url:", data["ubicacion_url"])
    time.sleep(0.05)

    # 4. Título principal
    h1 = soup.find("h1", class_="title-property")
    data["titulo"] = h1.get_text(strip=True) if h1 else ""
    print("titulo:", data["titulo"])
    time.sleep(0.05)

    # 5. Descripción completa
    desc_section = soup.find("section", class_="article-section-description")
    if desc_section:
        long_desc = desc_section.find("div", id="longDescription")
        data["descripcion"] = long_desc.get_text(" ", strip=True) if long_desc else ""
    else:
        data["descripcion"] = ""
    print("descripcion:", data["descripcion"])
    time.sleep(0.05)

    # 7. Información del anunciante
    anunciante = soup.find("h3", attrs={"data-qa": "linkMicrositioAnunciante"})
    data["anunciante"] = anunciante.get_text(strip=True) if anunciante else ""
    print("anunciante:", data["anunciante"])
    time.sleep(0.05)

    # 8. Códigos del anuncio
    codes_section = soup.find("section", id="reactPublisherCodes")
    if codes_section:
        lis = codes_section.find_all("li")
        codigo_anunciante = ""
        codigo_inmuebles24 = ""
        for li in lis:
            text = li.get_text(" ", strip=True)
            if "Cód. del anunciante" in text:
                parts = text.split(":")
                codigo_anunciante = parts[1].strip() if len(parts) > 1 else ""
            elif "Cód. Inmuebles24" in text:
                parts = text.split(":")
                codigo_inmuebles24 = parts[1].strip() if len(parts) > 1 else ""
        data["codigo_anunciante"] = codigo_anunciante
        data["codigo_inmuebles24"] = codigo_inmuebles24
    else:
        data["codigo_anunciante"] = data["codigo_inmuebles24"] = ""
    print("codigo_anunciante:", data["codigo_anunciante"])
    time.sleep(0.05)
    print("codigo_inmuebles24:", data["codigo_inmuebles24"])
    time.sleep(0.05)

    # 9. Tiempo de publicación
    user_views = soup.find("div", id="user-views")
    if user_views:
        p = user_views.find("p")
        data["tiempo_publicacion"] = p.get_text(strip=True) if p else ""
    else:
        data["tiempo_publicacion"] = ""
    print("tiempo_publicacion:", data["tiempo_publicacion"])
    time.sleep(0.05)

    # 10. Información del listado de iconos
    features_ul = soup.find("ul", id="section-icon-features-property")
    if features_ul:
        lis = features_ul.find_all("li", class_="icon-feature")
        data["area_total"] = ""
        data["area_cubierta"] = ""
        data["banos_icon"] = ""
        data["estacionamientos_icon"] = ""
        data["recamaras_icon"] = ""
        data["medio_banos_icon"] = ""
        data["antiguedad_icon"] = ""

        for li in lis:
            icon = li.find("i")
            if not icon:
                continue

            classes = icon.get("class", [])
            raw_text = li.get_text(" ", strip=True)
            text = re.sub(r"\s+", " ", raw_text).strip()

            print("DEBUG => classes:", classes, "| text:", repr(text))

            if "icon-stotal" in classes:
                data["area_total"] = text
            elif "icon-scubierta" in classes:
                data["area_cubierta"] = text
            elif "icon-bano" in classes:
                data["banos_icon"] = text
            elif "icon-cochera" in classes:
                data["estacionamientos_icon"] = text
            elif "icon-dormitorio" in classes:
                data["recamaras_icon"] = text
            elif "icon-toilete" in classes:
                data["medio_banos_icon"] = text
            elif "icon-antiguedad" in classes:
                data["antiguedad_icon"] = text
    else:
        data["area_total"] = data["area_cubierta"] = data["banos_icon"] = ""
        data["estacionamientos_icon"] = data["recamaras_icon"] = data["medio_banos_icon"] = data["antiguedad_icon"] = ""

    print("area_total:", data["area_total"])
    time.sleep(0.05)
    print("area_cubierta:", data["area_cubierta"])
    time.sleep(0.05)
    print("banos_icon:", data["banos_icon"])
    time.sleep(0.05)
    print("estacionamientos_icon:", data["estacionamientos_icon"])
    time.sleep(0.05)
    print("recamaras_icon:", data["recamaras_icon"])
    time.sleep(0.05)
    print("medio_banos_icon:", data["medio_banos_icon"])
    time.sleep(0.05)

    return data

def extract_information_after_click(driver):
    """Extrae información de los botones colapsables haciendo clic en ellos."""
    info_botones = {}

    try:
        container = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, "reactGeneralFeatures"))
        )
       
        buttons = container.find_elements(By.TAG_NAME, "button")
        print(f"🔎 Se encontraron {len(buttons)} botones. Intentando extraer datos...\n")

        for button in buttons:
            try:
                span_btn = button.find_element(By.TAG_NAME, "span")
                button_text = span_btn.text.strip()
                print(f"➡️ Haciendo clic en: {button_text}")
                driver.execute_script("arguments[0].scrollIntoView(true);", button)
                time.sleep(0.5)
                driver.execute_script("arguments[0].click();", button)
               
                try:
                    details_container = WebDriverWait(container, 5).until(
                        EC.presence_of_element_located((By.XPATH, ".//div[2]"))
                    )
                except:
                    print(f"⚠️ No se encontró el contenedor de detalles para '{button_text}'. Intentando otra estrategia...")
                    details_container = container.find_elements(By.TAG_NAME, "div")[1]
               
                time.sleep(1)

                features = [elem.text.strip() for elem in details_container.find_elements(By.TAG_NAME, "span") if elem.text.strip()]
                info_botones[button_text] = "; ".join(features)
               
                print(f"📌 Información extraída de '{button_text}': {features}\n")

            except Exception as e:
                print(f"❌ No se pudo extraer información de '{button_text}': {e}\n")
   
    except Exception as e:
        print(f"❌ Error al buscar botones: {e}")
   
    return info_botones

def scrape_property_details(driver: Driver, url: str) -> Dict:
    """Navega a una URL y extrae todos los detalles de la propiedad."""
    driver.uc_open_with_reconnect(url, reconnect_time=4)
    
    try:
        driver.uc_gui_click_captcha()
        time.sleep(3)
        print("    ✅ Captcha manejado")
    except:
        print("    ℹ️ No se detectó captcha")
    
    time.sleep(5)
    
    try:
        driver.wait_for_element("h1.title-property", timeout=15)
    except:
        print("    ⚠️ No se encontró el título de la propiedad")
    
    html = driver.page_source
    data = scrape_property_detail_complete(driver, html)
    data["URL"] = url
    
    button_data = extract_information_after_click(driver)
    data.update(button_data)
    
    return data

def main():
    """
    Orquesta el scraping de detalles de propiedades desde un archivo CSV.
    """
    print("--- 🏁 Iniciando scraping HEADLESS de DETALLES de propiedades ---")
    
    # 1. Leer el archivo de URLs con fecha dinámica
    today_str = datetime.now().strftime('%Y-%m-%d')

    possible_filenames = ["inmuebles24-zapopan-departamentos-venta.csv"]

    urls_df = None
    input_path = None
    
    for filename in possible_filenames:
        input_path = os.path.join(DATA_DIR, today_str, filename)
        try:
            print(f"Intentando cargar: {input_path}")
            urls_df = pd.read_csv(input_path)
            print(f"✅ Archivo encontrado: {filename}")
            break
        except FileNotFoundError:
            print(f"❌ No encontrado: {filename}")
            continue
    
    if urls_df is None:
        print("🔍 Buscando archivos en fechas anteriores...")
        pattern = os.path.join(DATA_DIR, "*", "*.csv")
        csv_files = glob.glob(pattern)
        
        if csv_files:
            latest_file = max(csv_files, key=os.path.getmtime)
            print(f"📂 Usando archivo más reciente: {latest_file}")
            urls_df = pd.read_csv(latest_file)
            input_path = latest_file
        else:
            print(f"❌ Error: No se encontraron archivos de URLs. Ejecuta 'scrap_inmuebles_fast.py' primero.")
            return

    if 'url' not in urls_df.columns:
        print(f"❌ Error: El archivo no contiene la columna 'url'. Columnas disponibles: {urls_df.columns.tolist()}")
        return
        
    urls = urls_df["url"].tolist()
    print(f"📊 Se cargaron {len(urls)} URLs para procesar")
    
    # MODO PRODUCCIÓN: Procesar TODAS las URLs
    print("🚀 MODO PRODUCCIÓN: Procesando TODAS las URLs encontradas")

    # 2. Inicializar el navegador HEADLESS
    driver = Driver(
        browser="chrome", 
        uc=True, 
        headless=True,
        user_data_dir=None,
        disable_gpu=True,
        no_sandbox=True
    )
    print(f"🌐 Driver HEADLESS inicializado - EXTRACCIÓN COMPLETA")
    
    all_details = []
    output_dir = os.path.join(DATA_DIR, today_str)
    os.makedirs(output_dir, exist_ok=True)

    # 3. Iterar sobre las URLs
    try:
        for i, url in enumerate(urls, start=1):
            print(f"\n🔎 Procesando URL {i}/{len(urls)}: {url}")
            try:
                details = scrape_property_details(driver, url)
                all_details.append(details)
                print(f"    ✅ Detalles extraídos exitosamente.")
                
                # Guardado incremental cada 10 propiedades
                if len(all_details) % 10 == 0:
                    temp_df = pd.DataFrame(all_details)
                    temp_filename = f"inmuebles24-detalles-temp-{len(all_details)}.csv"
                    temp_path = os.path.join(output_dir, temp_filename)
                    temp_df.to_csv(temp_path, index=False)
                    print(f"    💾 Guardado incremental: {len(all_details)} registros")
                
                if i < len(urls):
                    import random
                    sleep_time = random.uniform(3, 6)
                    print(f"    😴 Pausa de {sleep_time:.1f}s antes de la siguiente URL...")
                    time.sleep(sleep_time)
                    
            except Exception as e:
                print(f"    ❌ Error al scrapear detalles de la URL: {e}")
    finally:
        driver.quit()

    # 4. Guardar los resultados finales
    if all_details:
        details_df = pd.DataFrame(all_details)
        details_filename = "inmuebles24-detalles-completos-FINAL.csv"
        details_output_path = os.path.join(output_dir, details_filename)
        
        details_df.to_csv(details_output_path, index=False)
        print(f"\n💾 Proceso completado. {len(details_df)} propiedades detalladas guardadas en: {details_output_path}")
        
        print(f"\n📋 RESUMEN DE CAMPOS EXTRAÍDOS:")
        print(f"📊 Total de registros procesados: {len(details_df)}")
        print(f"📋 Campos disponibles: {len(details_df.columns)}")
        
        key_fields = ['URL', 'titulo', 'tipo_propiedad', 'precio', 'direccion', 'Características generales', 'Servicios', 'Amenidades']
        for col in key_fields:
            if col in details_df.columns:
                filled_count = details_df[col].notna().sum()
                print(f"  ✅ {col}: {filled_count}/{len(details_df)} registros")
        
        print(f"\n🔍 Columnas completas del CSV: {list(details_df.columns)}")

if __name__ == "__main__":
    main()
