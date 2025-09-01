#!/usr/bin/env python3
"""
CYT Simplificado - Basado en el original funcionando
Migrado automáticamente desde scrapers originales
"""

import os
import sys
import pandas as pd
import datetime as dt
import re
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

class CytSimplifiedScraper:
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
        """Parsear HTML usando selectores optimizados del scraper original CYT"""
        columns = ['descripcion', 'ubicacion', 'url', 'precio', 'tipo', 'habitaciones', 'baños', 'estacionamientos', 'superficie', 'codigo']
        data = pd.DataFrame(columns=columns)
        soup = BeautifulSoup(html, 'html.parser')
        
        # Selectores optimizados basados en el scraper original de CYT
        property_card_selectors = [
            # Selectores específicos actuales de CasasyTerrenos
            "div[class*='mx-2'][class*='w-[320px]']",
            "div[class*='w-[320px]']",
            # Selectores del original CYT
            '.property-card',
            '.listing-item', 
            '.property-item',
            '.inmueble-item',
            'div[class*="property"]',
            'div[class*="inmueble"]',
            'div[class*="listing"]',
            'article',
            # Fallbacks genéricos
            'div[class*="card"]',
            'div[class*="resultado"]'
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
            temp_dict['tipo'] = 'venta'

            # Descripción/Título - selectores optimizados múltiples
            title_selectors = [
                # Actuales de CYT
                "span[class*='text-text-primary font-bold line-clamp-2']",
                "span[class*='text-text-primary']",
                "span[class*='font-bold']",
                # Del original
                'h2 a', 'h3 a', '.property-title a', '.titulo-inmueble a',
                'h2', 'h3', '.property-title', '.titulo-inmueble',
                '.title', 'a[href*="detalle"]', 'a[href*="propiedad"]'
            ]
            
            for selector in title_selectors:
                title_elem = card.select_one(selector)
                if title_elem:
                    title_text = title_elem.get_text(strip=True)
                    if title_text and len(title_text) > 5:
                        temp_dict['descripcion'] = title_text
                        break

            # URL - selectores optimizados múltiples
            link_selectors = [
                # Actuales de CYT
                "a[target='_blank']",
                "a[href*='casasyterrenos.com']",
                # Del original
                'a[href*="detalle"]', 'a[href*="propiedad"]', 'a[href*="inmueble"]',
                'h2 a', 'h3 a', '.property-title a',
                'a'  # Fallback
            ]
            
            for selector in link_selectors:
                link_elem = card.select_one(selector)
                if link_elem and link_elem.get('href'):
                    href = link_elem.get('href')
                    if href and isinstance(href, str) and not href.startswith('#'):
                        if href.startswith('http'):
                            temp_dict['url'] = href
                        elif href.startswith('/'):
                            temp_dict['url'] = 'https://www.casasyterrenos.com' + href
                        else:
                            temp_dict['url'] = href
                        break
                
            # Ubicación - selectores optimizados múltiples
            location_selectors = [
                # Actuales de CYT
                "span[class*='text-blue-cyt']:not([class*='font-bold'])",
                "span[class*='text-blue-cyt']",
                # Del original
                '.location', '.ubicacion', '.property-location', '.ubicacion-inmueble',
                '[class*="location"]', '[class*="ubicacion"]', '[class*="address"]'
            ]
            
            for selector in location_selectors:
                location_elem = card.select_one(selector)
                if location_elem:
                    location_text = location_elem.get_text(strip=True)
                    if location_text and len(location_text) > 3:
                        temp_dict['ubicacion'] = location_text
                        break

            # Precio - selectores optimizados múltiples
            price_selectors = [
                # Actuales de CYT
                "span[class*='text-blue-cyt font-bold']",
                "span[class*='font-bold'][class*='blue']",
                # Del original
                '.price', '.precio', '.property-price', '.precio-inmueble',
                '[class*="price"]', '[class*="precio"]', '[class*="cost"]'
            ]
            
            for selector in price_selectors:
                price_elem = card.select_one(selector)
                if price_elem:
                    price_text = price_elem.get_text(strip=True)
                    if price_text and ('$' in price_text or 'MXN' in price_text or 'USD' in price_text or any(char.isdigit() for char in price_text)):
                        temp_dict['precio'] = price_text
                        break

            # Características múltiples - selectores optimizados
            features_selectors = [
                # Actuales de CYT
                "p[class*='text-sm']",
                "p.text-sm",
                # Del original
                '.features p', '.caracteristicas p', '.details p',
                'div[class*="feature"] p', 'div[class*="detail"] p'
            ]
            
            features = []
            for selector in features_selectors:
                found_features = card.select(selector)
                if found_features:
                    features = found_features
                    break
            
            # Asignar características con validación
            if len(features) >= 4:
                # Habitaciones
                hab_text = features[0].get_text(strip=True) if features[0] else ""
                if hab_text and hab_text != '-':
                    temp_dict['habitaciones'] = hab_text
                
                # Baños
                ban_text = features[1].get_text(strip=True) if len(features) > 1 and features[1] else ""
                if ban_text and ban_text != '-':
                    temp_dict['baños'] = ban_text
                
                # Estacionamientos
                est_text = features[2].get_text(strip=True) if len(features) > 2 and features[2] else ""
                if est_text and est_text != '-':
                    temp_dict['estacionamientos'] = est_text
                
                # Superficie
                sup_text = features[3].get_text(strip=True) if len(features) > 3 and features[3] else ""
                if sup_text and sup_text != '-':
                    temp_dict['superficie'] = sup_text

            # Código de propiedad - selectores optimizados múltiples
            code_selectors = [
                # Actuales de CYT
                "span[string*='Código:']",
                # Del original
                '[class*="codigo"]', '[class*="code"]', '[class*="id"]',
                '*[id]', '*[data-id]', '*[data-property-id]'
            ]
            
            # Buscar código por texto
            codigo_spans = card.find_all("span")
            for span in codigo_spans:
                span_text = span.get_text(strip=True)
                if "Código:" in span_text:
                    codigo_text = span_text.replace("Código:", "").strip()
                    temp_dict['codigo'] = codigo_text if codigo_text else "null"
                    break
            else:
                # Buscar en atributos
                for selector in code_selectors:
                    elem = card.select_one(selector)
                    if elem:
                        if elem.get('id'):
                            temp_dict['codigo'] = str(elem['id'])
                            break
                        elif elem.get('data-id'):
                            temp_dict['codigo'] = str(elem['data-id'])
                            break
            
            # Si no encontramos algunos datos usando selectores, usar regex en texto completo
            if any(temp_dict[key] == "null" for key in ['habitaciones', 'baños', 'superficie']):
                card_text = card.get_text()
                
                # Buscar habitaciones por regex si no se encontró
                if temp_dict['habitaciones'] == "null":
                    patterns = [
                        r'(\d+)\s*(?:recámara|habitacion|bedroom|hab|rec|cuarto)',
                        r'(\d+)\s*(?:room|bedroom)',
                        r'rec[áa]maras?\s*(\d+)',
                        r'habitaciones?\s*(\d+)'
                    ]
                    for pattern in patterns:
                        match = re.search(pattern, card_text.lower())
                        if match:
                            temp_dict['habitaciones'] = match.group(1)
                            break
                
                # Buscar baños por regex si no se encontró
                if temp_dict['baños'] == "null":
                    patterns = [
                        r'(\d+(?:\.\d+)?)\s*(?:baño|bathroom|bath)',
                        r'(\d+\.5|half)\s*(?:bath)',
                        r'baños?\s*(\d+(?:\.\d+)?)',
                        r'bathrooms?\s*(\d+(?:\.\d+)?)'
                    ]
                    for pattern in patterns:
                        match = re.search(pattern, card_text.lower())
                        if match:
                            temp_dict['baños'] = match.group(1)
                            break
                
                # Buscar superficie por regex si no se encontró
                if temp_dict['superficie'] == "null":
                    patterns = [
                        r'(\d+(?:,\d+)?)\s*(?:m²|metros|sqm|mt2)',
                        r'(\d+)\s*(?:metro|sq)',
                        r'superficie[:\s]*(\d+(?:,\d+)?)',
                        r'área[:\s]*(\d+(?:,\d+)?)'
                    ]
                    for pattern in patterns:
                        match = re.search(pattern, card_text)
                        if match:
                            temp_dict['superficie'] = match.group(1).replace(',', '')
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
            urls_file = self.project_root / 'URLs' / f'cyt_urls.csv'
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
                    self.save_data(all_data, f"cyt-temp.csv")
                
                time.sleep(2)  # Pausa entre requests
        
        finally:
            driver.quit()
        
        # Guardar datos finales
        self.save_data(all_data, f"cyt-data.csv")
        print(f"Scraping completado. Total registros: {len(all_data)}")

def main():
    parser = argparse.ArgumentParser(description='Cyt Simplified Scraper')
    parser.add_argument('--headless', action='store_true', default=True, help='Ejecutar en modo headless')
    parser.add_argument('--gui', action='store_true', help='Ejecutar con GUI')
    parser.add_argument('--pages', type=int, default=10, help='Número máximo de páginas')
    parser.add_argument('--urls-file', help='Archivo CSV con URLs')
    parser.add_argument('--url', help='URL específica para probar')
    
    args = parser.parse_args()
    
    scraper = CytSimplifiedScraper(
        headless=not args.gui,
        max_pages=args.pages,
        urls_file=args.urls_file
    )
    
    if args.url:
        # Probar con URL específica
        print(f"Probando con URL específica: {args.url}")
        driver = scraper.create_driver()
        try:
            data = scraper.scrape_url(args.url, driver)
            scraper.save_data(data, "cyt-test.csv")
            print(f"Prueba completada. Total registros: {len(data)}")
        finally:
            driver.quit()
    else:
        scraper.run_from_urls_file()

if __name__ == "__main__":
    main()
