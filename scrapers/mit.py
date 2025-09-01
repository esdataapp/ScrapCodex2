#!/usr/bin/env python3
"""
MIT Simplificado - Basado en el original funcionando
Migrado automáticamente desde scrapers originales
"""

import os
import sys
import pandas as pd
import datetime as dt
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import argparse
import time
from pathlib import Path

# Configuración
DDIR = 'data/'

class MitSimplifiedScraper:
    def __init__(self, headless=True, max_pages=None, urls_file=None):
        self.headless = headless
        self.max_pages = max_pages or 100
        self.urls_file = urls_file
        self.project_root = Path(__file__).parent.parent
        self.data_dir = self.project_root / 'data'
        self.data_dir.mkdir(exist_ok=True)
    
    def create_driver(self):
        """Crear driver de Selenium con configuración básica"""
        options = Options()
        if self.headless:
            options.add_argument("--headless")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--no-sandbox")
        driver = webdriver.Chrome(options=options)
        driver.set_page_load_timeout(60)
        return driver
    
    def scrape_url(self, url, driver):
        """Implementar scraping específico - debe ser personalizado por cada scraper"""
        print(f"Scrapeando: {url}")
        
        try:
            driver.get(url)
            # Esperar que cargue la página
            WebDriverWait(driver, 30).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
            
            html = driver.page_source
            return self.parse_html(html)
            
        except Exception as e:
            print(f"Error scrapeando {url}: {e}")
            return pd.DataFrame()
    
    def parse_html(self, html):
        """Parsear HTML usando selectores optimizados del scraper original MIT"""
        columns = ['nombre', 'precio', 'ubicacion', 'habitaciones', 'baños', 'metros_cuadrados', 'amenidades', 'fecha_publicacion', 'agencia', 'descripcion', 'url']
        data = pd.DataFrame(columns=columns)
        soup = BeautifulSoup(html, 'html.parser')
        
        # Selectores optimizados basados en el scraper original
        property_card_selectors = [
            '.listing-card',
            '.ad-overview', 
            '.listing',
            '.property-item',
            '.serp-item',
            'div[class*="listing"]',
            'div[class*="card"]'
        ]
        
        cards = []
        for selector in property_card_selectors:
            found_cards = soup.select(selector)
            if found_cards:
                cards = found_cards
                print(f"Encontradas {len(cards)} tarjetas con selector: {selector}")
                break
        
        if not cards:
            print("No se encontraron tarjetas con ningún selector")
            return data

        for card in cards:
            temp_dict = {col: "null" for col in columns}
            
            # Título/Nombre - selectores optimizados
            title_selectors = [
                'h2 a', 'h3 a', '.listing-card__title a', 
                '.ad-overview__title a', '.title a',
                'h2', 'h3', '.title', 'a[href*="property"]'
            ]
            
            for selector in title_selectors:
                title_elem = card.select_one(selector)
                if title_elem:
                    title_text = title_elem.get_text(strip=True)
                    if title_text:
                        temp_dict['nombre'] = title_text
                        # También intentar obtener URL del título
                        if title_elem.name == 'a' and title_elem.get('href'):
                            href = title_elem['href']
                            if href.startswith('http'):
                                temp_dict['url'] = href
                            elif href.startswith('/'):
                                temp_dict['url'] = 'https://www.mitula.mx' + href
                        break
            
            # Precio - selectores optimizados
            price_selectors = [
                '.price', '.listing-card__price', '.ad-overview__price', 
                '.serp-price', '[class*="price"]', '[class*="cost"]'
            ]
            
            for selector in price_selectors:
                price_elem = card.select_one(selector)
                if price_elem:
                    price_text = price_elem.get_text(strip=True)
                    if price_text and ('$' in price_text or 'MXN' in price_text):
                        temp_dict['precio'] = price_text
                        break
            
            # Ubicación - selectores optimizados
            location_selectors = [
                '.location', '.listing-card__location', '.ad-overview__location',
                '.serp-location', '[class*="location"]', '[class*="address"]'
            ]
            
            for selector in location_selectors:
                location_elem = card.select_one(selector)
                if location_elem:
                    location_text = location_elem.get_text(strip=True)
                    if location_text and len(location_text) > 3:
                        temp_dict['ubicacion'] = location_text
                        break
            
            # Área/Metros cuadrados - selectores optimizados
            area_selectors = [
                '.size', '.surface', '.area', '.listing-card__size',
                '.ad-overview__size', '[class*="size"]', '[class*="area"]'
            ]
            
            for selector in area_selectors:
                area_elem = card.select_one(selector)
                if area_elem:
                    area_text = area_elem.get_text(strip=True)
                    if area_text and ('m²' in area_text or 'sqm' in area_text):
                        # Extraer solo el número
                        import re
                        numbers = re.findall(r'(\d+(?:,\d+)?)', area_text)
                        if numbers:
                            temp_dict['metros_cuadrados'] = numbers[0]
                        break
            
            # Habitaciones - selectores optimizados
            rooms_selectors = [
                '.rooms', '.bedrooms', '.listing-card__rooms',
                '.ad-overview__rooms', '[class*="room"]', '[class*="bedroom"]'
            ]
            
            for selector in rooms_selectors:
                rooms_elem = card.select_one(selector)
                if rooms_elem:
                    rooms_text = rooms_elem.get_text(strip=True)
                    if rooms_text:
                        # Extraer número
                        import re
                        numbers = re.findall(r'(\d+)', rooms_text)
                        if numbers:
                            temp_dict['habitaciones'] = numbers[0]
                        break
            
            # Baños - selectores optimizados
            bathroom_selectors = [
                '.bathrooms', '.listing-card__bathrooms', '.ad-overview__bathrooms',
                '[class*="bathroom"]', '[class*="bath"]'
            ]
            
            for selector in bathroom_selectors:
                bathroom_elem = card.select_one(selector)
                if bathroom_elem:
                    bathroom_text = bathroom_elem.get_text(strip=True)
                    if bathroom_text:
                        # Extraer número (puede incluir decimales)
                        import re
                        numbers = re.findall(r'(\d+(?:\.\d+)?)', bathroom_text)
                        if numbers:
                            temp_dict['baños'] = numbers[0]
                        break
            
            # Descripción - selectores optimizados
            desc_selectors = [
                '.description', '.listing-card__description', '.ad-overview__description',
                '[class*="description"]', 'p'
            ]
            
            for selector in desc_selectors:
                desc_elem = card.select_one(selector)
                if desc_elem:
                    desc_text = desc_elem.get_text(strip=True)
                    if desc_text and len(desc_text) > 50:  # Solo descripciones largas
                        temp_dict['descripcion'] = desc_text[:500]  # Limitar longitud
                        break
            
            # Características/Amenidades
            features_selectors = [
                '.features', '.characteristics', '.listing-card__features',
                '.ad-overview__features', '[class*="feature"]'
            ]
            
            features_list = []
            for selector in features_selectors:
                feature_elems = card.select(selector)
                for elem in feature_elems:
                    feature_text = elem.get_text(strip=True)
                    if feature_text and len(feature_text) < 100:  # Evitar textos muy largos
                        features_list.append(feature_text)
            
            if features_list:
                temp_dict['amenidades'] = " | ".join(features_list[:5])  # Máximo 5 características
            
            # URL - buscar enlaces adicionales si no se encontró en título
            if temp_dict['url'] == "null":
                link_selectors = ['a[href*="property"]', 'a[href*="casa"]', 'a[href*="departamento"]', 'a']
                for selector in link_selectors:
                    link_elem = card.select_one(selector)
                    if link_elem and link_elem.get('href'):
                        href = link_elem['href']
                        if href and not href.startswith('#'):
                            if href.startswith('http'):
                                temp_dict['url'] = href
                            elif href.startswith('/'):
                                temp_dict['url'] = 'https://www.mitula.mx' + href
                            break
            
            # Si no encontramos algunos datos básicos usando selectores, usar regex en texto completo
            card_text = card.get_text()
            
            # Buscar habitaciones por regex si no se encontró
            if temp_dict['habitaciones'] == "null":
                import re
                patterns = [r'(\d+)\s*(?:recámara|habitacion|bedroom|hab|rec)', r'(\d+)\s*(?:cuarto|room)']
                for pattern in patterns:
                    match = re.search(pattern, card_text.lower())
                    if match:
                        temp_dict['habitaciones'] = match.group(1)
                        break
            
            # Buscar baños por regex si no se encontró
            if temp_dict['baños'] == "null":
                patterns = [r'(\d+(?:\.\d+)?)\s*(?:baño|bathroom|bath)', r'(\d+\.5|half)\s*(?:bath)']
                for pattern in patterns:
                    match = re.search(pattern, card_text.lower())
                    if match:
                        temp_dict['baños'] = match.group(1)
                        break
            
            # Buscar metros cuadrados por regex si no se encontró
            if temp_dict['metros_cuadrados'] == "null":
                patterns = [r'(\d+(?:,\d+)?)\s*(?:m²|metros|sqm)', r'(\d+)\s*(?:metro)']
                for pattern in patterns:
                    match = re.search(pattern, card_text)
                    if match:
                        temp_dict['metros_cuadrados'] = match.group(1).replace(',', '')
                        break

            data = pd.concat([data, pd.DataFrame([temp_dict])], ignore_index=True)
        
        return data
    
    def save_data(self, df, filename):
        """Guardar datos en CSV"""
        if df.empty:
            print("No hay datos para guardar")
            return
        
        today_str = dt.date.today().isoformat()
        out_dir = self.data_dir / today_str
        out_dir.mkdir(exist_ok=True)
        
        filepath = out_dir / filename
        
        try:
            existing_df = pd.read_csv(filepath)
            final_df = pd.concat([existing_df, df], ignore_index=True)
        except FileNotFoundError:
            final_df = df
        
        final_df.to_csv(filepath, index=False)
        print(f"Datos guardados en: {filepath}")
    
    def run_from_urls_file(self):
        """Ejecutar usando archivo de URLs"""
        if not self.urls_file:
            urls_file = self.project_root / 'URLs' / f'mit_urls.csv'
        else:
            urls_file = Path(self.urls_file)
        
        if not urls_file.exists():
            print(f"Archivo de URLs no encontrado: {urls_file}")
            return
        
        print(f"Cargando URLs desde: {urls_file}")
        urls_df = pd.read_csv(urls_file)
        
        if 'URL' not in urls_df.columns:
            print("No se encontró columna 'URL' en el archivo")
            return
        
        urls = urls_df['URL'].head(self.max_pages).tolist()
        print(f"Procesando {len(urls)} URLs...")
        
        driver = self.create_driver()
        all_data = pd.DataFrame()
        
        try:
            for i, url in enumerate(urls, 1):
                print(f"[{i}/{len(urls)}] Procesando...")
                data = self.scrape_url(url, driver)
                all_data = pd.concat([all_data, data], ignore_index=True)
                
                if i % 10 == 0:
                    self.save_data(all_data, f"mit-temp.csv")
                
                time.sleep(2)  # Pausa entre requests
        
        finally:
            driver.quit()
        
        # Guardar datos finales
        self.save_data(all_data, f"mit-data.csv")
        print(f"Scraping completado. Total registros: {len(all_data)}")

def main():
    parser = argparse.ArgumentParser(description='Mit Simplified Scraper')
    parser.add_argument('--headless', action='store_true', default=True, help='Ejecutar en modo headless')
    parser.add_argument('--gui', action='store_true', help='Ejecutar con GUI')
    parser.add_argument('--pages', type=int, default=10, help='Número máximo de páginas')
    parser.add_argument('--urls-file', help='Archivo CSV con URLs')
    
    args = parser.parse_args()
    
    scraper = MitSimplifiedScraper(
        headless=not args.gui,
        max_pages=args.pages,
        urls_file=args.urls_file
    )
    
    scraper.run_from_urls_file()

if __name__ == "__main__":
    main()
