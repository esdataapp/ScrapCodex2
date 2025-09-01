#!/usr/bin/env python3
"""
INM24 Simplificado - Actualizado para Coordinador
Migrado automáticamente desde scrapers originales
Compatible con sistema de carpetas específico
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

class Inm24SimplifiedScraper:
    def __init__(self, headless=True, max_pages=None, urls_file=None, output_dir=None, output_file=None):
        self.headless = headless
        self.max_pages = max_pages or 100
        self.urls_file = urls_file
        self.output_dir = Path(output_dir) if output_dir else None
        self.output_file = output_file
        self.project_root = Path(__file__).parent.parent
        
        # Si no se especifica directorio de salida, usar el por defecto
        if not self.output_dir:
            self.data_dir = self.project_root / 'data'
            self.data_dir.mkdir(exist_ok=True)
        else:
            self.data_dir = self.output_dir
            self.data_dir.mkdir(parents=True, exist_ok=True)
    
    def create_driver(self):
        """Crear driver de Selenium con configuración básica"""
        options = Options()
        if self.headless:
            options.add_argument("--headless")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-gpu")
        options.add_argument("--window-size=1920,1080")
        
        # User agent para evitar detección
        options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36")
        
        driver = webdriver.Chrome(options=options)
        driver.set_page_load_timeout(60)
        return driver
    
    def scrape_url(self, url, driver):
        """Scraper específico para inmuebles24 - Primera fase: obtener URLs de propiedades"""
        print(f"Scrapeando: {url}")
        
        try:
            driver.get(url)
            # Esperar que cargue la página
            WebDriverWait(driver, 30).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
            
            # Pausa adicional para inmuebles24
            time.sleep(3)
            
            # Obtener URLs de propiedades individuales
            property_urls = []
            page_count = 0
            
            while page_count < self.max_pages:
                try:
                    # Obtener URLs de la página actual
                    urls_in_page = self.extract_property_urls(driver)
                    property_urls.extend(urls_in_page)
                    
                    print(f"Página {page_count + 1}: {len(urls_in_page)} URLs encontradas")
                    
                    # Intentar ir a la siguiente página
                    next_button = self.find_next_page_button(driver)
                    if not next_button:
                        print("No hay más páginas")
                        break
                    
                    # Click en siguiente página
                    driver.execute_script("arguments[0].click();", next_button)
                    time.sleep(4)  # Esperar carga
                    
                    page_count += 1
                    
                except Exception as e:
                    print(f"Error en página {page_count + 1}: {e}")
                    break
            
            # Crear DataFrame con URLs para la fase 2
            df = pd.DataFrame({
                'link': property_urls,
                'scraped_from': url,
                'timestamp': dt.datetime.now().isoformat()
            })
            
            print(f"Total URLs extraídas: {len(property_urls)}")
            return df
            
        except Exception as e:
            print(f"Error scrapeando {url}: {e}")
            return pd.DataFrame()
    
    def extract_property_urls(self, driver):
        """Extraer URLs de propiedades individuales de inmuebles24"""
        urls = []
        
        # Selectores para enlaces de propiedades en inmuebles24
        property_link_selectors = [
            # Selectores específicos de inmuebles24
            "h3[data-qa='POSTING_CARD_DESCRIPTION'] a",
            "[data-qa='POSTING_CARD_DESCRIPTION'] a",
            "a[href*='/inmuebles/']",
            "a[href*='inmuebles24.com']",
            ".postingCardLayout-module__posting-card-layout a",
            # Fallbacks
            "h2 a", "h3 a", ".posting-title a"
        ]
        
        for selector in property_link_selectors:
            try:
                elements = driver.find_elements(By.CSS_SELECTOR, selector)
                for element in elements:
                    href = element.get_attribute('href')
                    if href and self.is_valid_property_url(href):
                        full_url = self.normalize_url(href)
                        if full_url not in urls:
                            urls.append(full_url)
                
                if urls:  # Si encontramos URLs con este selector, no probar otros
                    break
                    
            except Exception as e:
                print(f"Error con selector {selector}: {e}")
                continue
        
        return urls
    
    def is_valid_property_url(self, url):
        """Verificar si es una URL válida de propiedad"""
        if not url:
            return False
        
        # Filtros para inmuebles24
        valid_patterns = [
            '/inmuebles/',
            'inmuebles24.com',
        ]
        
        invalid_patterns = [
            'javascript:',
            'mailto:',
            '#',
            '/ayuda/',
            '/contacto/',
            '/login'
        ]
        
        for pattern in invalid_patterns:
            if pattern in url.lower():
                return False
        
        for pattern in valid_patterns:
            if pattern in url.lower():
                return True
        
        return False
    
    def normalize_url(self, url):
        """Normalizar URL para inmuebles24"""
        if url.startswith('//'):
            return 'https:' + url
        elif url.startswith('/'):
            return 'https://www.inmuebles24.com' + url
        elif not url.startswith('http'):
            return 'https://www.inmuebles24.com/' + url
        return url
    
    def find_next_page_button(self, driver):
        """Encontrar botón de siguiente página en inmuebles24"""
        next_selectors = [
            # Selectores específicos de inmuebles24
            "a[data-qa='PAGING_NEXT']",
            ".paging-next",
            "a[aria-label='Siguiente']",
            ".pagination-next",
            # Fallbacks genéricos
            "a:contains('Siguiente')",
            "a:contains('>')",
            ".next"
        ]
        
        for selector in next_selectors:
            try:
                elements = driver.find_elements(By.CSS_SELECTOR, selector)
                for element in elements:
                    if element.is_enabled() and element.is_displayed():
                        return element
            except:
                continue
        
        return None
    
    def save_data(self, df, filename=None):
        """Guardar datos en CSV"""
        if df.empty:
            print("No hay datos para guardar")
            return
        
        if filename:
            filepath = self.data_dir / filename
        else:
            today_str = dt.date.today().isoformat()
            filepath = self.data_dir / f"inm24_urls_{today_str}.csv"
        
        try:
            # Si el archivo existe, verificar si agregar o sobrescribir
            if filepath.exists():
                existing_df = pd.read_csv(filepath)
                # Para URLs, generalmente queremos sobrescribir para evitar duplicados
                final_df = df
            else:
                final_df = df
            
            final_df.to_csv(filepath, index=False)
            print(f"URLs guardadas en: {filepath}")
            
        except Exception as e:
            print(f"Error guardando datos: {e}")
    
    def run_from_single_url(self, url):
        """Ejecutar scraping de una URL específica"""
        print(f"Procesando URL específica: {url}")
        
        driver = self.create_driver()
        
        try:
            data = self.scrape_url(url, driver)
            
            if not data.empty:
                # Nombre del archivo de salida
                if self.output_file:
                    filename = self.output_file
                else:
                    timestamp = dt.datetime.now().strftime('%Y%m%d_%H%M%S')
                    filename = f"inm24_urls_{timestamp}.csv"
                
                self.save_data(data, filename)
                print(f"Scraping completado. Total URLs: {len(data)}")
                return True
            else:
                print("No se encontraron URLs")
                return False
        
        finally:
            driver.quit()
    
    def run_from_urls_file(self):
        """Ejecutar usando archivo de URLs (método original)"""
        if not self.urls_file:
            urls_file = self.project_root / 'URLs' / 'inm24_urls.csv'
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
                
                if i % 5 == 0:  # Guardar cada 5 URLs procesadas
                    temp_filename = f"inm24_urls_temp_{i}.csv"
                    self.save_data(all_data, temp_filename)
                
                time.sleep(3)  # Pausa entre requests
        
        finally:
            driver.quit()
        
        # Guardar datos finales
        final_filename = self.output_file or "inm24_urls_final.csv"
        self.save_data(all_data, final_filename)
        print(f"Scraping completado. Total URLs: {len(all_data)}")

def main():
    parser = argparse.ArgumentParser(description='Inm24 Simplified Scraper - Fase 1: URLs')
    parser.add_argument('--headless', action='store_true', default=True, help='Ejecutar en modo headless')
    parser.add_argument('--gui', action='store_true', help='Ejecutar con GUI')
    parser.add_argument('--pages', type=int, default=50, help='Número máximo de páginas')
    parser.add_argument('--urls-file', help='Archivo CSV con URLs base')
    parser.add_argument('--url', help='URL específica para procesar')
    parser.add_argument('--output-dir', help='Directorio de salida')
    parser.add_argument('--output-file', help='Nombre del archivo de salida')
    
    args = parser.parse_args()
    
    scraper = Inm24SimplifiedScraper(
        headless=not args.gui,
        max_pages=args.pages,
        urls_file=args.urls_file,
        output_dir=args.output_dir,
        output_file=args.output_file
    )
    
    if args.url:
        # Procesar URL específica
        success = scraper.run_from_single_url(args.url)
        sys.exit(0 if success else 1)
    else:
        # Procesar desde archivo de URLs
        scraper.run_from_urls_file()

if __name__ == "__main__":
    main()
