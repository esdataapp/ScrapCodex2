import os
import pandas as pd
import datetime as dt
import time
import json
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

DDIR = 'data/'

def scrape_property_detail(driver, html):
    soup = BeautifulSoup(html, "html.parser")
    data = {}

    # 1. Información básica
    title_div = soup.find("div", class_="main-title")
    data["nombre"] = title_div.find("h1").get_text(strip=True) if title_div and title_div.find("h1") else ""
    
    ubicacion_div = soup.find("div", class_="view-map__text")
    data["ubicacion"] = ubicacion_div.get_text(strip=True) if ubicacion_div else ""
    
    desc_div = soup.find("div", id="description-text")
    data["descripcion"] = desc_div.get_text(" ", strip=True) if desc_div else ""
    
    price_div = soup.find("div", class_="prices-and-fees__price")
    data["precio"] = price_div.get_text(strip=True) if price_div else ""

    # 2. Datos de place-details: habitaciones, baños, medios baños y área
    bedrooms_div = soup.find("div", attrs={"data-test": "bedrooms-value"})
    data["habitaciones"] = bedrooms_div.get_text(strip=True) if bedrooms_div else ""
    
    bathrooms_div = soup.find("div", attrs={"data-test": "full-bathrooms-value"})
    data["baños"] = bathrooms_div.get_text(strip=True) if bathrooms_div else ""
    
    half_bathrooms_div = soup.find("div", attrs={"data-test": "half-bathrooms-value"})
    data["medios_baños"] = half_bathrooms_div.get_text(strip=True) if half_bathrooms_div else ""
    
    area_div = soup.find("div", attrs={"data-test": "area-value"})
    data["metros_cuadrados"] = area_div.get_text(strip=True) if area_div else ""

    # 3. Place features: se extraen las 6 variables
    property_type_span = soup.find("span", attrs={"data-test": "property-type-value"})
    data["tipo_vivienda"] = property_type_span.get_text(strip=True) if property_type_span else ""
    
    operation_type_span = soup.find("span", attrs={"data-test": "operation-type-value"})
    data["tipo_operacion"] = operation_type_span.get_text(strip=True) if operation_type_span else ""
    
    construction_year_span = soup.find("span", attrs={"data-test": "construction-year-value"})
    data["año_construccion"] = construction_year_span.get_text(strip=True) if construction_year_span else ""
    
    condition_span = soup.find("span", attrs={"data-test": "condition-value"})
    data["estado"] = condition_span.get_text(strip=True) if condition_span else ""
    
    floor_span = soup.find("span", attrs={"data-test": "floor-value"})
    data["planta"] = floor_span.get_text(strip=True) if floor_span else ""
    
    floor_area_span = soup.find("span", attrs={"data-test": "floor-area-value"})
    data["superficie_construida"] = floor_area_span.get_text(strip=True) if floor_area_span else ""

    # 4. Fecha y publicación (por ejemplo, "17 ene 2025 - Publicado por ...")
    date_div = soup.find("div", class_="date")
    data["fecha_publicacion"] = date_div.get_text(strip=True) if date_div else ""

    # 5. Extraer facilidades (facilities)
    facilidades_propiedad = []
    facilidades_edificio = []
    facilities_divs = soup.find_all("div", class_="facilities")
    for fac in facilities_divs:
        title_el = fac.find("div", class_="facilities__title")
        if title_el:
            title_text = title_el.get_text(strip=True).lower()
            ul_elements = fac.find_all("ul")
            items = []
            for ul in ul_elements:
                li_elements = ul.find_all("li")
                for li in li_elements:
                    span_el = li.find("span")
                    if span_el:
                        items.append(span_el.get_text(strip=True))
                    else:
                        items.append(li.get_text(strip=True))
            if "propiedad" in title_text:
                facilidades_propiedad.extend(items)
            elif "edificio" in title_text:
                facilidades_edificio.extend(items)
    data["facilidades_propiedad"] = "; ".join(facilidades_propiedad)
    data["facilidades_edificio"] = "; ".join(facilidades_edificio)

    # Imprimir cada variable con un delay de 0.05 segundos para verificación
    for key, value in data.items():
        print(f"{key}: {value}")
        time.sleep(0.05)

    return data

def save(data_dict):
    today_str = dt.date.today().isoformat()
    out_dir = os.path.join(DDIR, today_str)
    os.makedirs(out_dir, exist_ok=True)
    fname = os.path.join(out_dir, "lamudi_detalle.csv")

    df_new = pd.DataFrame([data_dict])
    try:
        df_existing = pd.read_csv(fname, encoding="utf-8")
    except FileNotFoundError:
        df_existing = pd.DataFrame()

    final_df = pd.concat([df_existing, df_new], ignore_index=True)
    final_df = final_df.replace(r'[\r\n]+', ' ', regex=True)
    final_df.to_csv(fname, index=False, encoding="utf-8")
    print(f"Datos guardados en: {fname}")

def main():
    urls_df = pd.read_csv("data/2025-08-31/lamudi-guadalajara-venta.csv")
    urls = urls_df["url"].tolist()

    options = Options()
    options.add_argument("--headless")  # Modo headless habilitado
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")

    for i, URL in enumerate(urls, start=1):
        print(f"Iteración {i} de {len(urls)}: {URL}")
        print(f"\nNavegando a: {URL}")
        driver = webdriver.Chrome(options=options)
        driver.set_page_load_timeout(60)
        try:
            driver.get(URL)
            WebDriverWait(driver, 30).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "div.main-title h1"))
            )
            time.sleep(2)  # Pausa adicional para asegurar que la página cargue por completo

            html = driver.page_source
            data = scrape_property_detail(driver, html)
            save(data)
        except Exception as e:
            print(f"Error al procesar {URL}: {e}")
        finally:
            driver.quit()
        time.sleep(2)

if __name__ == "__main__":
    main()
