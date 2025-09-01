#!/usr/bin/env python3
"""
LAM Simplificado - Basado en el original funcionando
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

class LamSimplifiedScraper:
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
        """Parsear HTML usando selectores optimizados del scraper original LAM"""
        columns = ['nombre', 'descripcion', 'ubicacion', 'url', 'precio', 'tipo', 'habitaciones', 'baños', 'metros_cuadrados', 'estacionamientos']
        data = pd.DataFrame(columns=columns)
        soup = BeautifulSoup(html, 'html.parser')
        
        # Selectores optimizados basados en el scraper original de LAM
        property_card_selectors = [
            # Selectores específicos del original de Lamudi
            "[data-testid='listing-card']",
            ".ListingCell-row",
            ".listing-item",
            # Selectores actuales de Lamudi
            "div.snippet.js-snippet.normal",
            "div.snippet",
            # Fallbacks genéricos
            'div[class*="property"]',
            'div[class*="listing"]',
            'div[class*="card"]',
            'article'
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

            # Título/Nombre - selectores optimizados múltiples
            title_selectors = [
                # Del original LAM
                "[data-testid='listing-card-title'] a",
                ".ListingCell-KeyInfo-title a", 
                ".listing-title a",
                "h3 a", "h2 a",
                # Actuales de Lamudi
                "span.snippet__content__title",
                ".snippet__content__title",
                # Fallbacks
                ".title a", ".property-title a"
            ]
            
            for selector in title_selectors:
                title_elem = card.select_one(selector)
                if title_elem:
                    title_text = title_elem.get_text(strip=True)
                    if title_text and len(title_text) > 3:
                        temp_dict['nombre'] = title_text
                        # También intentar obtener URL del título
                        if title_elem.name == 'a' and title_elem.get('href'):
                            href = title_elem.get('href')
                            if href and isinstance(href, str):
                                if href.startswith('http'):
                                    temp_dict['url'] = href
                                elif href.startswith('/'):
                                    temp_dict['url'] = 'https://www.lamudi.com.mx' + href
                        break

            # URL - selectores optimizados múltiples si no se encontró en título
            if temp_dict['url'] == "null":
                link_selectors = [
                    # Del original LAM
                    "[data-testid='listing-card-title'] a",
                    ".ListingCell-KeyInfo-title a",
                    # Actuales de Lamudi
                    "a[href*='lamudi.com']",
                    "a",  # Fallback
                ]
                
                for selector in link_selectors:
                    link_elem = card.select_one(selector)
                    if link_elem and link_elem.get('href'):
                        href = link_elem.get('href')
                        if href and isinstance(href, str) and not href.startswith('#'):
                            if href.startswith('http'):
                                temp_dict['url'] = href
                            elif href.startswith('/'):
                                temp_dict['url'] = 'https://www.lamudi.com.mx' + href
                            break

            # Descripción - selectores optimizados múltiples
            desc_selectors = [
                # Actuales de Lamudi
                "div.snippet__content__description",
                ".snippet__content__description",
                # Del original LAM
                ".ListingCell-KeyInfo-description",
                ".listing-description",
                # Fallbacks
                ".description", "p"
            ]
            
            for selector in desc_selectors:
                desc_elem = card.select_one(selector)
                if desc_elem:
                    desc_text = desc_elem.get_text(strip=True)
                    if desc_text and len(desc_text) > 10:  # Solo descripciones largas
                        temp_dict['descripcion'] = desc_text[:500]  # Limitar longitud
                        break

            # Ubicación - selectores optimizados múltiples
            location_selectors = [
                # Del original LAM
                "[data-testid='listing-card-location']",
                ".ListingCell-KeyInfo-address",
                ".listing-location", ".location", ".address",
                # Actuales de Lamudi
                "span[data-test='snippet-content-location']",
                "[data-test='snippet-content-location']",
                # Fallbacks
                '[class*="location"]', '[class*="address"]'
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
                # Del original LAM
                "[data-testid='listing-card-price']",
                ".ListingCell-KeyInfo-price",
                ".listing-price", ".price", ".precio",
                # Actuales de Lamudi
                "div.snippet__content__price",
                ".snippet__content__price",
                # Fallbacks
                '[class*="price"]', '[class*="precio"]'
            ]
            
            for selector in price_selectors:
                price_elem = card.select_one(selector)
                if price_elem:
                    price_text = price_elem.get_text(strip=True)
                    if price_text and ('$' in price_text or 'MXN' in price_text or 'USD' in price_text or any(char.isdigit() for char in price_text)):
                        temp_dict['precio'] = price_text
                        break

            # Habitaciones - selectores optimizados múltiples
            bedrooms_selectors = [
                # Del original LAM
                "[data-testid='listing-card-bedrooms']",
                "[data-testid='bedrooms-value']",
                # Actuales de Lamudi
                "span[data-test='bedrooms-value']",
                "[data-test='bedrooms-value']",
                # Fallbacks
                '[class*="bedroom"]', '[class*="habitacion"]', '[class*="rec"]'
            ]
            
            for selector in bedrooms_selectors:
                bedrooms_elem = card.select_one(selector)
                if bedrooms_elem:
                    bedrooms_text = bedrooms_elem.get_text(strip=True)
                    if bedrooms_text and bedrooms_text.replace(' ', '').isdigit():
                        temp_dict['habitaciones'] = bedrooms_text
                        break

            # Baños - selectores optimizados múltiples
            bathrooms_selectors = [
                # Del original LAM
                "[data-testid='listing-card-bathrooms']",
                "[data-testid='bathrooms-value']", 
                # Actuales de Lamudi
                "span[data-test='full-bathrooms-value']",
                "[data-test='full-bathrooms-value']",
                "[data-test='bathrooms-value']",
                # Fallbacks
                '[class*="bathroom"]', '[class*="baño"]', '[class*="bath"]'
            ]
            
            for selector in bathrooms_selectors:
                bathrooms_elem = card.select_one(selector)
                if bathrooms_elem:
                    bathrooms_text = bathrooms_elem.get_text(strip=True)
                    if bathrooms_text and (bathrooms_text.replace('.', '').replace(' ', '').isdigit() or bathrooms_text in ['0.5', '1.5', '2.5']):
                        temp_dict['baños'] = bathrooms_text
                        break

            # Superficie/Área - selectores optimizados múltiples
            area_selectors = [
                # Del original LAM
                "[data-testid='listing-card-area']",
                "[data-testid='area-value']",
                # Actuales de Lamudi
                "span[data-test='area-value']",
                "[data-test='area-value']",
                # Fallbacks
                '[class*="area"]', '[class*="superficie"]', '[class*="m2"]'
            ]
            
            for selector in area_selectors:
                area_elem = card.select_one(selector)
                if area_elem:
                    area_text = area_elem.get_text(strip=True)
                    if area_text and ('m²' in area_text or 'mt2' in area_text or any(char.isdigit() for char in area_text)):
                        # Extraer solo el número
                        numbers = re.findall(r'(\d+(?:,\d+)?)', area_text)
                        if numbers:
                            temp_dict['metros_cuadrados'] = numbers[0].replace(',', '')
                        else:
                            temp_dict['metros_cuadrados'] = area_text
                        break

            # Estacionamientos - selectores optimizados múltiples
            parking_selectors = [
                # Del original LAM
                "[data-testid='listing-card-parking']",
                "[data-testid='parking-value']",
                # Actuales de Lamudi
                "span[data-test='parking-value']", 
                "[data-test='parking-value']",
                # Fallbacks
                '[class*="parking"]', '[class*="estacionamiento"]', '[class*="garage"]'
            ]
            
            for selector in parking_selectors:
                parking_elem = card.select_one(selector)
                if parking_elem:
                    parking_text = parking_elem.get_text(strip=True)
                    if parking_text and parking_text.replace(' ', '').isdigit():
                        temp_dict['estacionamientos'] = parking_text
                        break

            # Si no encontramos algunos datos usando selectores, usar regex en texto completo
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
            if temp_dict['metros_cuadrados'] == "null":
                patterns = [
                    r'(\d+(?:,\d+)?)\s*(?:m²|metros|sqm|mt2)',
                    r'(\d+)\s*(?:metro|sq)',
                    r'superficie[:\s]*(\d+(?:,\d+)?)',
                    r'área[:\s]*(\d+(?:,\d+)?)'
                ]
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
            urls_file = self.project_root / 'URLs' / f'lam_urls.csv'
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
                    self.save_data(all_data, f"lam-temp.csv")
                
                time.sleep(2)  # Pausa entre requests
        
        finally:
            driver.quit()
        
        # Guardar datos finales
        self.save_data(all_data, f"lam-data.csv")
        print(f"Scraping completado. Total registros: {len(all_data)}")

def main():
    parser = argparse.ArgumentParser(description='Lam Simplified Scraper')
    parser.add_argument('--headless', action='store_true', default=True, help='Ejecutar en modo headless')
    parser.add_argument('--gui', action='store_true', help='Ejecutar con GUI')
    parser.add_argument('--pages', type=int, default=10, help='Número máximo de páginas')
    parser.add_argument('--urls-file', help='Archivo CSV con URLs')
    parser.add_argument('--url', help='URL específica para probar')
    
    args = parser.parse_args()
    
    scraper = LamSimplifiedScraper(
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
            scraper.save_data(data, "lam-test.csv")
            print(f"Prueba completada. Total registros: {len(data)}")
        finally:
            driver.quit()
    else:
        scraper.run_from_urls_file()

if __name__ == "__main__":
    main()
