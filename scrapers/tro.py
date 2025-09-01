#!/usr/bin/env python3
"""
TRO Simplificado - Basado en el original funcionando
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

class TroSimplifiedScraper:
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
        """Parsear HTML usando selectores optimizados del scraper original TRO"""
        columns = ['name', 'location', 'price', 'description', 'url', 'tipo', 'area', 'rooms', 'bathrooms']
        data = pd.DataFrame(columns=columns)
        soup = BeautifulSoup(html, 'html.parser')
        
        def extract_with_fallback(element, selectors):
            """Función auxiliar para extraer texto con múltiples selectores"""
            for selector in selectors:
                try:
                    elem = element.select_one(selector)
                    if elem and elem.get_text(strip=True):
                        return elem.get_text(strip=True)
                except:
                    continue
            return None
        
        # Selectores para tarjetas de propiedades (no carruseles de imágenes)
        property_card_selectors = [
            # Más específicos para evitar carruseles
            '.search-result-item', '.listing-item', '.property-listing',
            'article[class*="listing"]', 'div[class*="result"]:not([class*="image"])',
            '.serp-item', '.ad-container', '.listing-container',
            # Del original TRO - específicos de Trovit
            '.listing-card', '.ad-overview', '.listing', '.property-item',
            # Fallbacks que excluyen imágenes
            'div[class*="listing"]:not([class*="image"]):not([class*="carousel"])',
            'div[class*="card"]:not([class*="image"])',
            'div[class*="item"]:not([class*="image"]):not([class*="carousel"])',
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

            # Título/Nombre - selectores más amplios
            title_selectors = [
                # Específicos de Trovit
                'h2 a', 'h3 a', 'h4 a', '.listing-card__title a', '.ad-overview__title a', '.title a',
                '.listing-title a', '.property-title a', '.result-title a',
                # Sin enlaces
                'h2', 'h3', 'h4', '.listing-card__title', '.ad-overview__title', '.title',
                '.listing-title', '.property-title', '.result-title',
                # Fallbacks muy amplios
                'a[title]', 'a', '[class*="title"]', '[class*="name"]'
            ]
            
            title_text = extract_with_fallback(card, title_selectors)
            if title_text and len(title_text) > 3:
                temp_dict['name'] = title_text
                temp_dict['description'] = title_text
            else:
                # Si no encontramos título, usar texto del primer enlace o texto general
                first_link = card.find('a')
                if first_link and first_link.get_text(strip=True):
                    title_text = first_link.get_text(strip=True)
                    if len(title_text) > 5 and len(title_text) < 200:
                        temp_dict['name'] = title_text
                        temp_dict['description'] = title_text

            # URL - selectores del original TRO
            link_selectors = [
                # Del original TRO
                'h2 a', 'h3 a', '.listing-card__title a', '.ad-overview__title a', '.title a',
                # Actuales de Trovit
                '.listing-title a', '.property-title a', '.result-title a',
                # Fallbacks
                "a[href*='trovit.com']", "a"
            ]
            
            for selector in link_selectors:
                try:
                    link_elem = card.select_one(selector)
                    if link_elem and link_elem.get('href'):
                        href = link_elem.get('href')
                        if href and isinstance(href, str) and not href.startswith('#'):
                            if href.startswith('http'):
                                temp_dict['url'] = href
                            elif href.startswith('/'):
                                temp_dict['url'] = 'https://casas.trovit.com.mx' + href
                            break
                except:
                    continue

            # Precio - selectores del original TRO
            price_selectors = [
                # Del original TRO
                '.price', '.listing-card__price', '.ad-overview__price', '.serp-price',
                # Actuales de Trovit
                '.result-price', '.property-price', '.cost', '.amount',
                # Fallbacks
                '[class*="price"]', '[class*="precio"]', '[class*="cost"]'
            ]
            
            price_text = extract_with_fallback(card, price_selectors)
            if price_text and ('$' in price_text or 'MXN' in price_text or 'USD' in price_text or any(char.isdigit() for char in price_text)):
                temp_dict['price'] = price_text

            # Ubicación - selectores del original TRO
            location_selectors = [
                # Del original TRO
                '.location', '.listing-card__location', '.ad-overview__location', '.serp-location',
                # Actuales de Trovit
                '.result-location', '.property-location', '.address', '.zone',
                # Fallbacks
                '[class*="location"]', '[class*="address"]', '[class*="zone"]'
            ]
            
            location_text = extract_with_fallback(card, location_selectors)
            if location_text and len(location_text) > 3:
                temp_dict['location'] = location_text

            # Área/Superficie - selectores del original TRO
            area_selectors = [
                # Del original TRO
                '.size', '.surface', '.area', '.listing-card__size', '.ad-overview__size',
                # Actuales de Trovit
                '.result-size', '.property-size', '.dimensions',
                # Fallbacks
                '[class*="size"]', '[class*="area"]', '[class*="surface"]'
            ]
            
            area_text = extract_with_fallback(card, area_selectors)
            if area_text:
                temp_dict['area'] = area_text

            # Habitaciones - selectores del original TRO
            rooms_selectors = [
                # Del original TRO
                '.rooms', '.bedrooms', '.listing-card__rooms', '.ad-overview__rooms',
                # Actuales de Trovit
                '.result-rooms', '.property-rooms', '.dormitorios',
                # Fallbacks
                '[class*="room"]', '[class*="bedroom"]', '[class*="dormitorio"]'
            ]
            
            rooms_text = extract_with_fallback(card, rooms_selectors)
            if rooms_text:
                temp_dict['rooms'] = rooms_text

            # Baños - selectores del original TRO
            bathrooms_selectors = [
                # Del original TRO
                '.bathrooms', '.listing-card__bathrooms', '.ad-overview__bathrooms',
                # Actuales de Trovit
                '.result-bathrooms', '.property-bathrooms', '.banos',
                # Fallbacks
                '[class*="bathroom"]', '[class*="bano"]', '[class*="bath"]'
            ]
            
            bathrooms_text = extract_with_fallback(card, bathrooms_selectors)
            if bathrooms_text:
                temp_dict['bathrooms'] = bathrooms_text

            # Si no encontramos algunos datos usando selectores, usar regex en texto completo
            card_text = card.get_text()
            
            # Buscar precio por regex si no se encontró
            if temp_dict['price'] == "null":
                price_patterns = [
                    r'\$[\s]*[\d,]+(?:\.\d{2})?(?:\s*(?:MXN|USD|pesos))?',
                    r'[$]?\s*\d{1,3}(?:,\d{3})*(?:\.\d{2})?\s*(?:MXN|USD|pesos|mill?(?:ó|o)n)?',
                    r'(?:Precio|Price|Desde|From|Venta|Sale|Renta|Rent|Costo|Cost)[:\s]*\$?[\s]*[\d,]+(?:\.\d{2})?',
                    r'\d{1,3}(?:,\d{3})*\s*(?:mil|thousand|mill|k|K)',
                    r'[\d,]+(?:\.\d{2})?\s*(?:MXN|USD|pesos)',
                    r'(?:MXN|USD)[\s]*[\d,]+(?:\.\d{2})?',
                    r'\d{4,}(?:,\d{3})*(?:\.\d{2})?'
                ]
                for pattern in price_patterns:
                    match = re.search(pattern, card_text, re.IGNORECASE)
                    if match:
                        temp_dict['price'] = match.group(0).strip()
                        break
            
            # Buscar ubicación por regex si no se encontró
            if temp_dict['location'] == "null":
                location_patterns = [
                    r'(?:en|ubicado en|location)\s+([^,\n]+(?:,\s*[^,\n]+)*)',
                    r'([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*,\s*(?:Jalisco|CDMX|DF|Ciudad de México))',
                    r'(Col\.\s+[^,\n]+)',
                    r'([^,\n]+,\s*(?:Jalisco|CDMX|DF|Ciudad de México))',
                    r'(Zapopan|Guadalajara|Tlaquepaque|Tonalá)[^,\n]*'
                ]
                for pattern in location_patterns:
                    match = re.search(pattern, card_text, re.IGNORECASE)
                    if match:
                        temp_dict['location'] = match.group(1).strip()
                        break
            
            # Buscar área por regex si no se encontró
            if temp_dict['area'] == "null":
                area_patterns = [
                    r'(\d+\.?\d*)\s*m[²2]',
                    r'(\d+\.?\d*)\s*metros\s*cuadrados',
                    r'Area[:\s]*(\d+\.?\d*)',
                    r'Superficie[:\s]*(\d+\.?\d*)'
                ]
                for pattern in area_patterns:
                    match = re.search(pattern, card_text, re.IGNORECASE)
                    if match:
                        temp_dict['area'] = match.group(0).strip()
                        break
            
            # Buscar habitaciones por regex si no se encontró
            if temp_dict['rooms'] == "null":
                rooms_patterns = [
                    r'(\d+)\s*(?:hab|habitacion|bedroom|cuarto)',
                    r'(?:hab|habitacion|bedroom|cuarto)[:\s]*(\d+)',
                    r'(\d+)\s*rec[aá]mara'
                ]
                for pattern in rooms_patterns:
                    match = re.search(pattern, card_text, re.IGNORECASE)
                    if match:
                        temp_dict['rooms'] = match.group(1).strip() + ' hab'
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
            urls_file = self.project_root / 'URLs' / f'tro_urls.csv'
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
                    self.save_data(all_data, f"tro-temp.csv")
                
                time.sleep(2)  # Pausa entre requests
        
        finally:
            driver.quit()
        
        # Guardar datos finales
        self.save_data(all_data, f"tro-data.csv")
        print(f"Scraping completado. Total registros: {len(all_data)}")

def main():
    parser = argparse.ArgumentParser(description='Tro Simplified Scraper')
    parser.add_argument('--headless', action='store_true', default=True, help='Ejecutar en modo headless')
    parser.add_argument('--gui', action='store_true', help='Ejecutar con GUI')
    parser.add_argument('--pages', type=int, default=10, help='Número máximo de páginas')
    parser.add_argument('--urls-file', help='Archivo CSV con URLs')
    parser.add_argument('--url', help='URL específica para probar')
    
    args = parser.parse_args()
    
    scraper = TroSimplifiedScraper(
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
            scraper.save_data(data, "tro-test.csv")
            print(f"Prueba completada. Total registros: {len(data)}")
        finally:
            driver.quit()
    else:
        scraper.run_from_urls_file()

if __name__ == "__main__":
    main()
