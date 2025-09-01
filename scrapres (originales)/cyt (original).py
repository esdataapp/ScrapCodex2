import os
import pandas as pd
import datetime as dt
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

DDIR = 'data/'

URL_BASE = "https://www.casasyterrenos.com/jalisco/zapopan/departamentos/venta?desde=0&hasta=1000000000&utm_source=results_page="


def scrape_page_source(html):
    columns = ['descripcion', 'ubicacion', 'url', 'precio', 'tipo', 'habitaciones', 'baños', 'estacionamientos', 'superficie', 'codigo']
    data = pd.DataFrame(columns=columns)
    soup = BeautifulSoup(html, 'html.parser')
    cards = soup.find_all("div", class_=lambda x: x and "mx-2" in x and "w-[320px]" in x)

    for card in cards:
        temp_dict = {col: None for col in columns}
        temp_dict['tipo'] = 'venta'

        # Descripción y URL
        link = card.find("a", target="_blank")
        if link:
            descripcion_span = card.find("span", class_=lambda x: x and "text-text-primary font-bold line-clamp-2" in x)
            temp_dict['descripcion'] = descripcion_span.get_text(strip=True) if descripcion_span else None
            temp_dict['url'] = link.get('href', None)
            
        # Ubicación
        ubicacion_span = card.find("span", class_=lambda x: x and "text-blue-cyt" in x)
        temp_dict['ubicacion'] = ubicacion_span.get_text(strip=True) if ubicacion_span else None

        # Precio
        precio_span = card.find("span", class_=lambda x: x and "text-blue-cyt font-bold" in x)
        temp_dict['precio'] = precio_span.get_text(strip=True) if precio_span else None

        # Características (Habitaciones, Baños, Estacionamientos, Superficie)
        features = card.find_all("p", class_=lambda x: x and "text-sm" in x)
        if len(features) >= 4:
            temp_dict['habitaciones'] = features[0].get_text(strip=True)
            temp_dict['baños'] = features[1].get_text(strip=True)
            temp_dict['estacionamientos'] = features[2].get_text(strip=True)
            temp_dict['superficie'] = features[3].get_text(strip=True)

        # Código de la propiedad
        codigo_span = card.find("span", class_=lambda x: x and "text-extralight" in x)
        if codigo_span:
            temp_dict['codigo'] = codigo_span.get_text(strip=True).replace("Código: ", "")

        data = pd.concat([data, pd.DataFrame([temp_dict])], ignore_index=True)
    
    return data


def save(df_page):
    today_str = dt.date.today().isoformat()
    out_dir = os.path.join(DDIR, today_str)
    os.makedirs(out_dir, exist_ok=True)
    fname = os.path.join(out_dir, "casasyterrenos-departamento-zapopan-venta.csv")
    try:
        df_existing = pd.read_csv(fname)
    except FileNotFoundError:
        df_existing = pd.DataFrame()
    final_df = pd.concat([df_existing, df_page], ignore_index=True)
    final_df.to_csv(fname, index=False)
    print(f"Datos guardados en: {fname}")


def main():
    total_pages = 120  # Número de páginas a recorrer
    options = Options()
    options.add_argument("--headless")
    driver = webdriver.Chrome(options=options)
    driver.set_page_load_timeout(60)

    for i in range(90, total_pages + 1):
        URL = f"{URL_BASE}{i}"
        print(f"Scrapeando página {i} de {total_pages}")
        
        try:
            driver.get(URL)
            WebDriverWait(driver, 30).until(EC.presence_of_element_located((By.XPATH, "//div[contains(@class, 'mx-2') and contains(@class, 'w-[320px]')]")))
            html = driver.page_source
            df_page = scrape_page_source(html)
            save(df_page)
        except Exception as e:
            print(f"Error en la página {i}: {e}")
        
    driver.quit()
    print("Scraping completado.")


if __name__ == "__main__":
    main()