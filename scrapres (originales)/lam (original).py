import os
import pandas as pd
import datetime as dt
from bs4 import BeautifulSoup
from seleniumbase import Driver
import time

DDIR = 'data/'

def scrape_page_source(html):
    columns = ['nombre', 'descripcion', 'ubicacion', 'url', 'precio', 'tipo', 'habitaciones', 'baños', 'metros_cuadrados', 'estacionamientos']
    data = pd.DataFrame(columns=columns)
    soup = BeautifulSoup(html, 'html.parser')
    cards = soup.find_all("div", class_="snippet js-snippet normal")

    for card in cards:
        temp_dict = {col: None for col in columns}
        temp_dict['tipo'] = 'venta'

        # Nombre y URL de la propiedad
        title_span = card.find("span", class_="snippet__content__title")
        if title_span:
            temp_dict['nombre'] = title_span.get_text(strip=True)
        
        link_a = card.find("a", href=True)
        if link_a:
            temp_dict['url'] = "https://www.lamudi.com.mx" + link_a['href']
        
        # Descripción
        desc_div = card.find("div", class_="snippet__content__description")
        if desc_div:
            temp_dict['descripcion'] = desc_div.get_text(strip=True)
        
        # Ubicación
        loc_span = card.find("span", attrs={"data-test": "snippet-content-location"})
        if loc_span:
            temp_dict['ubicacion'] = loc_span.get_text(strip=True)
        
        # Precio
        price_div = card.find("div", class_="snippet__content__price")
        if price_div:
            temp_dict['precio'] = price_div.get_text(strip=True)
        
        # Características (habitaciones, baños, metros cuadrados, estacionamientos)
        rooms_span = card.find("span", attrs={"data-test": "bedrooms-value"})
        if rooms_span:
            temp_dict['habitaciones'] = rooms_span.get_text(strip=True)
        
        bathrooms_span = card.find("span", attrs={"data-test": "full-bathrooms-value"})
        if bathrooms_span:
            temp_dict['baños'] = bathrooms_span.get_text(strip=True)
        
        area_span = card.find("span", attrs={"data-test": "area-value"})
        if area_span:
            temp_dict['metros_cuadrados'] = area_span.get_text(strip=True)
        
        parking_span = card.find("span", attrs={"data-test": "amenity-value"})
        if parking_span:
            temp_dict['estacionamientos'] = parking_span.get_text(strip=True)
        
        data = pd.concat([data, pd.DataFrame([temp_dict])], ignore_index=True)
    return data

def save(df_page):
    today_str = dt.date.today().isoformat()
    out_dir = os.path.join(DDIR, today_str)
    os.makedirs(out_dir, exist_ok=True)
    fname = os.path.join(out_dir, "lamudi-guadalajara-venta.csv")
    try:
        df_existing = pd.read_csv(fname)
    except FileNotFoundError:
        df_existing = pd.DataFrame()
    final_df = pd.concat([df_existing, df_page], ignore_index=True)
    final_df.to_csv(fname, index=False)
    print(f"Datos guardados en: {fname}")

def main():
    i = 1
    total_urls = 63
    while i <= total_urls:   
        URL = f'https://www.lamudi.com.mx/jalisco/zapopan/departamento/for-sale/?page={i}'
        print(f"Iteración {i} of {total_urls}")
        driver = Driver(uc=True)
        i += 1
        try:
            print(f"Navegando a: {URL}")
            driver.uc_open_with_reconnect(URL, 4)
            driver.uc_gui_click_captcha()
            
            html = driver.page_source
            df_page = scrape_page_source(html)
            save(df_page)
        except Exception as e:
            print(f"Error al cargar la página: {e}")
        finally:
            driver.quit()

if __name__ == "__main__":
    main()