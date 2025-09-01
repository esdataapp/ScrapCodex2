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

def scrape_page_source(html):
    columns = ['nombre', 'precio', 'ubicacion', 'habitaciones', 'baños', 'metros_cuadrados', 'amenidades', 'fecha_publicacion', 'agencia', 'descripcion', 'url']
    data = pd.DataFrame(columns=columns)
    soup = BeautifulSoup(html, 'html.parser')
    cards = soup.find_all("div", class_="listing-card__content")

    for card in cards:
        temp_dict = {col: None for col in columns}
        
        # Nombre/Título
        title_span = card.find("span", {"data-test": "snippet__title"})
        if title_span:
            temp_dict['nombre'] = title_span.get_text(strip=True)
        
        # Precio
        price_span = card.find("span", {"data-test": "price__actual"})
        if price_span:
            temp_dict['precio'] = price_span.get_text(strip=True)
        
        # Ubicación
        location_div = card.find("div", {"data-test": "snippet__location"})
        if location_div:
            temp_dict['ubicacion'] = location_div.get_text(strip=True)
        
        # Habitaciones
        bedrooms_p = card.find("p", {"data-test": "bedrooms"})
        if bedrooms_p:
            temp_dict['habitaciones'] = bedrooms_p.get_text(strip=True)
        
        # Baños
        bathrooms_p = card.find("p", {"data-test": "bathrooms"})
        if bathrooms_p:
            temp_dict['baños'] = bathrooms_p.get_text(strip=True)
        
        # Metros cuadrados
        area_p = card.find("p", {"data-test": "floor-area"})
        if area_p:
            temp_dict['metros_cuadrados'] = area_p.get_text(strip=True)
        
        # Amenidades
        amenities = card.find_all("span", class_="listing-card__facilities__facility")
        temp_dict['amenidades'] = ", ".join([amenity.get_text(strip=True) for amenity in amenities]) if amenities else None
        
        # Fecha de publicación y agencia (Manejo de errores)
        pub_info_p = card.find("p", {"data-test": "snippet__published-date-and-agency"})
        if pub_info_p:
            pub_info_text = pub_info_p.get_text(strip=True)
            parts = pub_info_text.split("-", 1)  # Dividir solo en dos partes
            temp_dict['fecha_publicacion'] = parts[0].strip()
            temp_dict['agencia'] = parts[1].strip() if len(parts) > 1 else None
        
        # Descripción
        desc_div = card.find("div", {"data-test": "snippet__description"})
        if desc_div:
            temp_dict['descripcion'] = desc_div.get_text(strip=True)
        
        # URL del anuncio (Obtenida desde el botón "Ver en detalle")
        detail_button = card.find("button", {"data-test": "snippet__view-detail-button"})
        if detail_button:
            parent = detail_button.find_parent("a")  # Buscar enlace en el padre
            if parent and parent.get("href"):
                temp_dict['url'] = f"https://casas.mitula.mx{parent.get('href')}"
        
        data = pd.concat([data, pd.DataFrame([temp_dict])], ignore_index=True)
    
    return data

def save(df_page):
    today_str = dt.date.today().isoformat()
    out_dir = os.path.join(DDIR, today_str)
    os.makedirs(out_dir, exist_ok=True)
    fname = os.path.join(out_dir, "mitula-zapopan-venta.csv")
    try:
        df_existing = pd.read_csv(fname)
    except FileNotFoundError:
        df_existing = pd.DataFrame()
    final_df = pd.concat([df_existing, df_page], ignore_index=True)
    final_df.to_csv(fname, index=False)
    print(f"Datos guardados en: {fname}")

def main():
    total_urls = 100  # Número de páginas a scrapear
    for i in range(1, total_urls + 1):
        URL = f'https://casas.mitula.mx/find?page={i}&operationType=sell&geoId=mitula-MX-poblacion-0000531914&text=Zapopan%2C++%28Jalisco%29'
        print(f"Iteración {i} of {total_urls}")
        options = Options()
        options.add_argument("--headless")  # Ejecutar sin interfaz gráfica
        driver = webdriver.Chrome(options=options)
        driver.set_page_load_timeout(60)
        
        try:
            print(f"Navegando a: {URL}")
            driver.get(URL)
            WebDriverWait(driver, 30).until(EC.presence_of_element_located((By.CLASS_NAME, "listing-card__content")))
            html = driver.page_source
            df_page = scrape_page_source(html)
            save(df_page)
        except Exception as e:
            print(f"Error al cargar la página: {e}")
        finally:
            driver.quit()

if __name__ == "__main__":
    main()
