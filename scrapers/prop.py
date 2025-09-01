#!/usr/bin/env python3
"""
PROP Ultra Evasion - Técnicas de evasión extremas
Implementa bypass de Cloudflare Turnstile y anti-detección máxima
"""

import undetected_chromedriver as uc
import time
import random
import json
import requests
from bs4 import BeautifulSoup
import pandas as pd
from pathlib import Path
import argparse

class PropUltraEvasion:
    def __init__(self):
        self.project_root = Path(__file__).parent.parent
        self.data_dir = self.project_root / 'data'
        self.data_dir.mkdir(exist_ok=True)
        
        # Configuración ultra stealth
        self.setup_ultra_config()
    
    def setup_ultra_config(self):
        """Configuración de ultra evasión"""
        
        # User agents ultra-realistas actuales
        self.ultra_user_agents = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 Edg/120.0.0.0",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
        ]
        
        # Headers ultra-realistas
        self.ultra_headers = {
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br',
            'Accept-Language': 'es-MX,es;q=0.9,en;q=0.8,en-US;q=0.7',
            'Cache-Control': 'max-age=0',
            'Sec-Ch-Ua': '"Not_A Brand";v="8", "Chromium";v="120", "Google Chrome";v="120"',
            'Sec-Ch-Ua-Mobile': '?0',
            'Sec-Ch-Ua-Platform': '"Windows"',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Sec-Fetch-User': '?1',
            'Upgrade-Insecure-Requests': '1',
            'Connection': 'keep-alive',
        }
    
    def create_ultra_stealth_driver(self):
        """Crear driver con undetected-chrome para máxima evasión"""
        print("🦾 Creando driver ultra-stealth con undetected-chrome...")
        
        # Configuración de undetected-chrome
        options = uc.ChromeOptions()
        
        # User agent aleatorio
        user_agent = random.choice(self.ultra_user_agents)
        options.add_argument(f"--user-agent={user_agent}")
        
        # Viewport aleatorio realista
        viewports = [
            "--window-size=1920,1080",
            "--window-size=1366,768", 
            "--window-size=1536,864",
            "--window-size=1440,900"
        ]
        options.add_argument(random.choice(viewports))
        
        # Configuración anti-detección extrema
        options.add_argument("--no-first-run")
        options.add_argument("--no-service-autorun") 
        options.add_argument("--password-store=basic")
        options.add_argument("--use-mock-keychain")
        options.add_argument("--disable-component-extensions-with-background-pages")
        options.add_argument("--disable-default-apps")
        options.add_argument("--disable-extensions")
        options.add_argument("--disable-background-timer-throttling")
        options.add_argument("--disable-backgrounding-occluded-windows")
        options.add_argument("--disable-renderer-backgrounding")
        options.add_argument("--disable-features=TranslateUI")
        options.add_argument("--disable-ipc-flooding-protection")
        
        # Locale específico
        options.add_argument("--lang=es-MX")
        
        # Crear driver con undetected-chrome
        driver = uc.Chrome(options=options, version_main=None)
        
        print(f"🚀 Driver ultra-stealth creado con User-Agent: {user_agent[:50]}...")
        
        return driver
    
    def bypass_cloudflare_manual(self, driver, url, max_attempts=3):
        """Intento de bypass manual de Cloudflare"""
        print("🛡️ Intentando bypass de Cloudflare...")
        
        for attempt in range(max_attempts):
            print(f"🔄 Intento {attempt + 1}/{max_attempts}")
            
            try:
                # Navegar a la URL
                driver.get(url)
                
                # Esperar tiempo extra para carga
                time.sleep(random.uniform(10, 20))
                
                # Verificar si hay challenge
                page_source = driver.page_source.lower()
                
                # Indicadores de challenge de Cloudflare
                cf_indicators = [
                    'checking your browser',
                    'please wait',
                    'just a moment',
                    'challenge-form',
                    'turnstile',
                    'cf-browser-verification'
                ]
                
                has_challenge = any(indicator in page_source for indicator in cf_indicators)
                
                if has_challenge:
                    print(f"🔍 Challenge detectado en intento {attempt + 1}")
                    
                    # Esperar más tiempo para auto-resolución
                    print("⏳ Esperando resolución automática...")
                    time.sleep(random.uniform(20, 40))
                    
                    # Verificar de nuevo
                    page_source = driver.page_source.lower()
                    has_challenge = any(indicator in page_source for indicator in cf_indicators)
                    
                    if not has_challenge:
                        print("✅ Challenge resuelto automáticamente")
                        return True
                    else:
                        print("⚠️ Challenge persiste")
                        
                        if attempt < max_attempts - 1:
                            print("🔄 Reiniciando driver...")
                            driver.quit()
                            time.sleep(random.uniform(5, 10))
                            driver = self.create_ultra_stealth_driver()
                else:
                    print("✅ Sin challenge detectado")
                    return True
                    
            except Exception as e:
                print(f"❌ Error en intento {attempt + 1}: {e}")
                if attempt < max_attempts - 1:
                    time.sleep(random.uniform(5, 10))
        
        print("❌ No se pudo bypasear Cloudflare")
        return False
    
    def try_requests_fallback(self, url):
        """Fallback usando requests con sesión persistente"""
        print("🔄 Intentando fallback con requests...")
        
        session = requests.Session()
        
        # Headers ultra-realistas
        headers = self.ultra_headers.copy()
        headers['User-Agent'] = random.choice(self.ultra_user_agents)
        
        session.headers.update(headers)
        
        try:
            # Primera request para obtener cookies
            print("🍪 Obteniendo cookies iniciales...")
            response = session.get("https://propiedades.com", timeout=30)
            time.sleep(random.uniform(2, 5))
            
            # Request a la URL objetivo
            print(f"🎯 Accediendo a URL objetivo...")
            response = session.get(url, timeout=30)
            
            if response.status_code == 200:
                # Verificar si hay contenido válido
                if 'propiedades' in response.text.lower() and 'challenge' not in response.text.lower():
                    print("✅ Requests exitoso - sin challenge")
                    return response.text
                else:
                    print("⚠️ Requests recibió challenge")
            else:
                print(f"❌ Requests falló: {response.status_code}")
                
        except Exception as e:
            print(f"❌ Error en requests: {e}")
        
        return None
    
    def parse_html_ultra(self, html):
        """Parsing ultra-agresivo de HTML"""
        print("🔍 Parsing ultra-agresivo...")
        
        columns = ['name', 'location', 'price', 'description', 'url', 'tipo']
        data = pd.DataFrame(columns=columns)
        soup = BeautifulSoup(html, 'html.parser')
        
        # Análisis exhaustivo de la estructura
        print("📊 Analizando estructura de página...")
        
        # Contar elementos relevantes
        all_divs = soup.find_all('div')
        all_links = soup.find_all('a')
        text_with_dollar = soup.find_all(string=lambda text: text and '$' in text)
        
        print(f"📈 Estadísticas de página:")
        print(f"   Divs totales: {len(all_divs)}")
        print(f"   Links totales: {len(all_links)}")
        print(f"   Textos con '$': {len(text_with_dollar)}")
        
        # Si hay texto con $, es buena señal
        if text_with_dollar:
            print("💰 Precios detectados en el texto")
            for i, text in enumerate(text_with_dollar[:3]):
                print(f"   Precio {i+1}: {text.strip()[:50]}")
        
        # Búsqueda ultra-exhaustiva de tarjetas
        ultra_selectors = [
            # Selectores específicos
            ".ad", ".property-card", ".listing-card", ".property-item",
            ".listing-item", ".result-item", ".search-result",
            
            # Por atributos
            "[data-property]", "[data-listing]", "[data-ad]",
            "[data-item]", "[data-card]", "[data-result]",
            
            # Por ID
            "[id*='property']", "[id*='listing']", "[id*='result']",
            
            # Por clases parciales
            "[class*='property']", "[class*='listing']", "[class*='result']",
            "[class*='card']", "[class*='item']", "[class*='ad']",
            
            # Contenedores con links
            "div:has(a[href*='inmueble'])",
            "div:has(a[href*='propiedad'])",
            "div:has(a[href*='terreno'])",
            
            # Contenedores con precios
            "div:has(*:contains('$'))",
            
            # Fallbacks genéricos
            "article", "section", "li",
            "div[class]", "span[class]"
        ]
        
        cards = []
        successful_selector = None
        
        for selector in ultra_selectors:
            try:
                found_cards = soup.select(selector)
                # Filtrar elementos que parezcan tarjetas de propiedades
                valid_cards = []
                
                for card in found_cards:
                    card_text = card.get_text().lower()
                    # Verificar si contiene indicadores de propiedad
                    property_indicators = ['venta', 'renta', 'precio', '$', 'terreno', 'casa', 'departamento', 'm²', 'ubicación']
                    indicator_count = sum(1 for indicator in property_indicators if indicator in card_text)
                    
                    # Si tiene al menos 2 indicadores y contenido sustancial
                    if indicator_count >= 2 and len(card_text) > 50:
                        valid_cards.append(card)
                
                if len(valid_cards) > 0:
                    cards = valid_cards
                    successful_selector = selector
                    print(f"✅ Encontradas {len(cards)} tarjetas válidas con: {selector}")
                    break
                    
            except Exception as e:
                continue
        
        if not cards:
            print("❌ No se encontraron tarjetas de propiedades válidas")
            
            # Análisis de debugging avanzado
            print("\n🔍 ANÁLISIS DE DEBUGGING:")
            
            # Buscar patrones comunes
            common_patterns = ['propiedad', 'inmueble', 'venta', 'renta', 'precio', 'ubicación']
            for pattern in common_patterns:
                elements = soup.find_all(string=lambda text: text and pattern in text.lower())
                if elements:
                    print(f"   '{pattern}' encontrado en {len(elements)} elementos")
            
            return data
        
        print(f"🏠 Procesando {len(cards)} tarjetas válidas...")
        
        # Procesamiento ultra-exhaustivo de tarjetas
        for i, card in enumerate(cards):
            try:
                temp_dict = {col: "null" for col in columns}
                temp_dict['tipo'] = 'venta'
                
                card_text = card.get_text()
                
                # Nombre/Título - búsqueda ultra-agresiva
                title_found = False
                title_selectors = [
                    "h1", "h2", "h3", "h4", "h5", ".title", ".name", ".titulo",
                    ".property-title", ".ad-title", ".listing-title",
                    "a[href*='inmueble']", "a[href*='propiedad']", "a"
                ]
                
                for selector in title_selectors:
                    try:
                        title_elem = card.select_one(selector)
                        if title_elem:
                            title_text = title_elem.get_text(strip=True)
                            if title_text and len(title_text) > 10:
                                temp_dict['name'] = title_text[:200]
                                temp_dict['description'] = title_text[:200]
                                title_found = True
                                break
                    except:
                        continue
                
                # Si no encontró título, usar primer texto largo
                if not title_found:
                    sentences = [s.strip() for s in card_text.split('.') if len(s.strip()) > 20]
                    if sentences:
                        temp_dict['name'] = sentences[0][:200]
                        temp_dict['description'] = sentences[0][:200]
                
                # URL - búsqueda exhaustiva
                all_links = card.find_all('a', href=True)
                for link in all_links:
                    href = link.get('href', '')
                    if href and not href.startswith('#') and not href.startswith('javascript:'):
                        if 'inmueble' in href or 'propiedad' in href or 'terreno' in href:
                            if href.startswith('/'):
                                temp_dict['url'] = 'https://propiedades.com' + href
                            elif href.startswith('http'):
                                temp_dict['url'] = href
                            break
                
                # Precio - regex ultra-agresivo
                import re
                price_patterns = [
                    r'\$[\s]*[\d,]+(?:\.\d{2})?(?:\s*(?:MXN|USD|pesos))?',
                    r'[$]?\s*\d{1,3}(?:,\d{3})*(?:\.\d{2})?\s*(?:MXN|USD|pesos|mill?(?:ó|o)n)?',
                    r'(?:Precio|Price|Desde|From|Venta|Sale|Renta|Rent|Costo|Cost)[:\s]*\$?[\s]*[\d,]+',
                    r'\d{1,3}(?:,\d{3})*\s*(?:mil|thousand|mill|k|K)',
                    r'[\d,]+(?:\.\d{2})?\s*(?:MXN|USD|pesos)',
                    r'(?:MXN|USD)[\s]*[\d,]+',
                    r'\d{4,}(?:,\d{3})*'
                ]
                
                for pattern in price_patterns:
                    match = re.search(pattern, card_text, re.IGNORECASE)
                    if match:
                        price_text = match.group(0).strip()
                        # Validar que sea un precio realista
                        if any(char.isdigit() for char in price_text):
                            temp_dict['price'] = price_text[:50]
                            break
                
                # Ubicación - regex exhaustivo
                location_patterns = [
                    r'(?:en|ubicado en|location)\s+([^,\n]+)',
                    r'([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*,\s*(?:Jalisco|Guadalajara|Zapopan))',
                    r'(Col\.\s+[^,\n]+)',
                    r'([^,\n]+,\s*(?:Jalisco|Guadalajara|Zapopan))',
                    r'(Zapopan|Guadalajara|Tlaquepaque|Tonalá)[^,\n]*'
                ]
                
                for pattern in location_patterns:
                    match = re.search(pattern, card_text, re.IGNORECASE)
                    if match:
                        location_text = match.group(1).strip() if match.lastindex >= 1 else match.group(0).strip()
                        if len(location_text) > 3:
                            temp_dict['location'] = location_text[:100]
                            break
                
                # Solo agregar si tiene información mínima
                if (temp_dict['name'] != "null" or 
                    temp_dict['price'] != "null" or 
                    temp_dict['url'] != "null"):
                    data = pd.concat([data, pd.DataFrame([temp_dict])], ignore_index=True)
                
            except Exception as e:
                print(f"⚠️ Error procesando tarjeta {i+1}: {e}")
                continue
        
        print(f"✅ Extraídas {len(data)} propiedades con ultra-parsing")
        return data
    
    def scrape_with_ultra_evasion(self, url):
        """Scraping con técnicas de ultra-evasión"""
        print(f"🦾 Iniciando ultra-evasión para: {url}")
        
        # Método 1: Undetected Chrome
        print("\n=== MÉTODO 1: UNDETECTED CHROME ===")
        driver = None
        try:
            driver = self.create_ultra_stealth_driver()
            
            if self.bypass_cloudflare_manual(driver, url):
                html = driver.page_source
                data = self.parse_html_ultra(html)
                if len(data) > 0:
                    print("✅ Éxito con undetected-chrome")
                    return data
        except Exception as e:
            print(f"❌ Error con undetected-chrome: {e}")
        finally:
            if driver:
                try:
                    driver.quit()
                except:
                    pass
        
        # Método 2: Requests con sesión
        print("\n=== MÉTODO 2: REQUESTS AVANZADO ===")
        html = self.try_requests_fallback(url)
        if html:
            data = self.parse_html_ultra(html)
            if len(data) > 0:
                print("✅ Éxito con requests")
                return data
        
        print("❌ Todos los métodos de ultra-evasión fallaron")
        return pd.DataFrame()

def main():
    parser = argparse.ArgumentParser(description='PROP Ultra Evasion Scraper')
    parser.add_argument('--url', required=True, help='URL para probar ultra-evasión')
    
    args = parser.parse_args()
    
    scraper = PropUltraEvasion()
    data = scraper.scrape_with_ultra_evasion(args.url)
    
    if len(data) > 0:
        # Guardar resultados
        output_file = scraper.data_dir / "prop_ultra_evasion_results.csv"
        data.to_csv(output_file, index=False)
        print(f"\n💾 Resultados guardados en: {output_file}")
        print(f"📊 Total registros: {len(data)}")
        
        # Mostrar muestra
        print(f"\n=== MUESTRA DE RESULTADOS ===")
        for i, row in data.head(3).iterrows():
            print(f"\nPropiedad {i+1}:")
            for col in ['name', 'price', 'location', 'url']:
                if col in row and row[col] != 'null':
                    value = str(row[col])[:80] + "..." if len(str(row[col])) > 80 else str(row[col])
                    print(f"  {col}: {value}")
    else:
        print("\n❌ Ultra-evasión no pudo extraer datos")
        print("💡 Sugerencias:")
        print("  • El sitio puede tener protecciones muy avanzadas")
        print("  • Considerar usar proxies premium")
        print("  • Probar en horarios de menor tráfico")
        print("  • Implementar solving de CAPTCHA")

if __name__ == "__main__":
    main()
