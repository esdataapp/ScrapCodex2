#!/usr/bin/env python3
"""
Scraper de Inmuebles24 - Versión HEADLESS para Ubuntu Server
Con sistema avanzado de monitoreo y detección de bloqueos
OPTIMIZADO CON PAUSAS DEL SCRIPT ORIGINAL
"""
import os
import pandas as pd
import datetime as dt
from bs4 import BeautifulSoup
from seleniumbase import Driver
import time
import random
import logging
import json
from pathlib import Path

# --- Configuración ---
# Para Ubuntu Server (usar chrome estándar)
CHROME_PATH = None  # Usar None para que use el chrome del sistema
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(os.path.dirname(BASE_DIR), 'data')
LOGS_DIR = os.path.join(os.path.dirname(BASE_DIR), 'logs')

# Crear directorio de logs si no existe
os.makedirs(LOGS_DIR, exist_ok=True)

# Configurar logging avanzado
def setup_logging():
    """Configura sistema de logging detallado."""
    log_filename = f"scraper_{dt.datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
    log_path = os.path.join(LOGS_DIR, log_filename)
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_path, encoding='utf-8'),
            logging.StreamHandler()  # También mostrar en consola
        ]
    )
    
    logger = logging.getLogger(__name__)
    logger.info(f"📝 Sistema de logging iniciado - Archivo: {log_path}")
    return logger

def save_page_debug(url, page_source, page_num, status="success"):
    """Guarda una muestra del HTML de la página para debug."""
    debug_dir = os.path.join(LOGS_DIR, "page_samples")
    os.makedirs(debug_dir, exist_ok=True)
    
    timestamp = dt.datetime.now().strftime('%Y%m%d_%H%M%S')
    filename = f"page_{page_num:03d}_{status}_{timestamp}.html"
    filepath = os.path.join(debug_dir, filename)
    
    # Guardar solo los primeros 10000 caracteres para no llenar el disco
    sample_html = page_source[:10000] if len(page_source) > 10000 else page_source
    
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(f"<!-- URL: {url} -->\n")
        f.write(f"<!-- Timestamp: {timestamp} -->\n")
        f.write(f"<!-- Status: {status} -->\n")
        f.write(f"<!-- Page length: {len(page_source)} chars -->\n\n")
        f.write(sample_html)
    
    return filepath

def detect_blocking_or_issues(driver, page_source, url):
    """Detecta si la página está siendo bloqueada o tiene problemas."""
    issues = []
    current_url = driver.current_url
    page_title = driver.title.lower()
    
    # Detectar redirecciones sospechosas
    if current_url != url:
        issues.append(f"REDIRECCION: {url} -> {current_url}")
    
    # Detectar Cloudflare
    cloudflare_indicators = [
        "cloudflare", "cf-ray", "checking your browser", "ddos protection",
        "security check", "ray id", "cloudflare-nginx", "un momento"
    ]
    
    for indicator in cloudflare_indicators:
        if indicator in page_source.lower():
            issues.append(f"CLOUDFLARE: Detectado '{indicator}' en la página")
    
    # Detectar otros sistemas de protección
    protection_indicators = [
        "access denied", "forbidden", "blocked", "bot detection",
        "too many requests", "rate limit", "captcha", "verify you are human"
    ]
    
    for indicator in protection_indicators:
        if indicator in page_source.lower():
            issues.append(f"PROTECCION: Detectado '{indicator}' en la página")
    
    # Detectar errores HTTP
    error_indicators = ["404", "500", "502", "503", "error", "not found"]
    for indicator in error_indicators:
        if indicator in page_title:
            issues.append(f"ERROR_HTTP: '{indicator}' en el título")
    
    # Verificar si hay contenido esperado
    expected_content = ["inmuebles24", "departamento", "precio", "zapopan"]
    content_found = sum(1 for content in expected_content if content in page_source.lower())
    
    if content_found < 2:
        issues.append(f"CONTENIDO_SOSPECHOSO: Solo {content_found}/4 indicadores esperados")
    
    return issues

def scrape_page_source(html, logger):
    """Extrae datos de las tarjetas de propiedades del HTML."""
    columns = ['nombre', 'descripcion', 'ubicacion', 'url', 'precio', 'tipo', 'habitaciones', 'baños']
    data = pd.DataFrame(columns=columns)
    soup = BeautifulSoup(html, 'html.parser')
    
    # Usar el selector que sabemos que funciona
    cards = soup.find_all("div", class_="postingCardLayout-module__posting-card-layout")
    logger.info(f"    🎯 Encontradas {len(cards)} tarjetas en la página")

    for card in cards:
        temp_dict = {col: None for col in columns}
        temp_dict['tipo'] = 'venta'
        
        # Extraer nombre y descripción
        desc_h3 = card.find("h3", {"data-qa": "POSTING_CARD_DESCRIPTION"})
        if desc_h3:
            link_a = desc_h3.find("a")
            if link_a:
                temp_dict['nombre'] = link_a.get_text(strip=True)
                temp_dict['descripcion'] = link_a.get_text(strip=True)
                temp_dict['url'] = "https://www.inmuebles24.com" + link_a.get('href', '')
        
        # Extraer precio
        price_div = card.find("div", {"data-qa": "POSTING_CARD_PRICE"})
        if price_div:
            temp_dict['precio'] = price_div.get_text(strip=True)
        
        # Extraer ubicación
        address_div = card.find("div", class_="postingLocations-module__location-address")
        address_txt = address_div.get_text(strip=True) if address_div else ""
        loc_h2 = card.find("h2", {"data-qa": "POSTING_CARD_LOCATION"})
        loc_txt = loc_h2.get_text(strip=True) if loc_h2 else ""
        temp_dict['ubicacion'] = f"{address_txt}, {loc_txt}" if address_txt and loc_txt else address_txt or loc_txt
        
        # Extraer características (habitaciones y baños)
        features = card.find("h3", {"data-qa": "POSTING_CARD_FEATURES"})
        if features:
            for sp in features.find_all("span"):
                txt = sp.get_text(strip=True).lower()
                if "rec" in txt:
                    temp_dict['habitaciones'] = txt
                if "bañ" in txt:
                    temp_dict['baños'] = txt
        
        # Solo agregar si tiene URL válida
        if temp_dict['url']:
            data = pd.concat([data, pd.DataFrame([temp_dict])], ignore_index=True)
    
    return data

def save(df_page, logger):
    """Guarda los datos en CSV con timestamp."""
    today_str = dt.date.today().isoformat()
    out_dir = os.path.join(DATA_DIR, today_str)
    os.makedirs(out_dir, exist_ok=True)
    fname = os.path.join(out_dir, "inmuebles24-zapopan-departamentos-venta.csv")
    
    try:
        df_existing = pd.read_csv(fname)
    except FileNotFoundError:
        df_existing = pd.DataFrame()
    
    final_df = pd.concat([df_existing, df_page], ignore_index=True)
    final_df.to_csv(fname, index=False)
    logger.info(f"    💾 Datos guardados en: {fname}")

def save_progress_report(page_num, successful_pages, failed_pages, issues_summary):
    """Guarda un reporte de progreso en JSON."""
    report = {
        "timestamp": dt.datetime.now().isoformat(),
        "current_page": page_num,
        "successful_pages": successful_pages,
        "failed_pages": failed_pages,
        "total_processed": page_num,
        "success_rate": f"{(successful_pages / page_num * 100):.1f}%",
        "issues_summary": issues_summary
    }
    
    report_path = os.path.join(LOGS_DIR, "progress_report.json")
    with open(report_path, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2, ensure_ascii=False)

def main():
    """Función principal - scraping completo con monitoreo avanzado."""
    logger = setup_logging()
    logger.info("--- 🏁 Iniciando scraping HEADLESS de Inmuebles24 Zapopan ---")
    
    # Calcular páginas totales estimadas - MODO CON PAUSAS ORIGINALES
    total_pages = 100  # Configuración para producción completa
    logger.info(f"📊 MODO PRODUCCIÓN: Procesando {total_pages} páginas con pausas del script original")
    
    successful_pages = 0
    failed_pages = 0
    consecutive_failures = 0
    all_issues = []
    
    for i in range(1, total_pages + 1):
        URL = f'https://www.inmuebles24.com/departamentos-en-venta-en-zapopan-pagina-{i}.html'
        logger.info(f"\n📄 Página {i}/{total_pages}: {URL}")
        
        # Crear driver nuevo para cada página con configuración mejorada
        try:
            # Configuración optimizada para evadir detección
            driver = Driver(
                browser="chrome", 
                binary_location=CHROME_PATH,  # None para usar chrome del sistema
                uc=True, 
                headless=True,  # MODO HEADLESS para servidor
                page_load_strategy="eager",  # Cargar más rápido
                ad_block_on=True,  # Bloquear anuncios
                block_images=True,  # No cargar imágenes para ser más rápido
                incognito=True  # Modo incógnito
            )
            logger.info("    🔧 Driver HEADLESS optimizado inicializado")
        except Exception as e:
            logger.error(f"    ❌ Error inicializando driver: {e}")
            failed_pages += 1
            continue
        
        page_issues = []
        
        try:
            # Pausa inicial conservadora como el script original
            initial_pause = random.uniform(2, 4)
            logger.info(f"    ⏳ Pausa inicial: {initial_pause:.1f}s")
            time.sleep(initial_pause)
            
            logger.info("    🌐 Navegando...")
            driver.uc_open_with_reconnect(URL, 4)
            
            # NO intentar manejar captcha en headless (causa errores)
            logger.info("    ⏳ Esperando carga completa...")
            # Usar tiempo de carga similar al original (más conservador)
            time.sleep(5)  # Tiempo fijo como el original
            
            # Obtener información de la página
            current_url = driver.current_url
            page_title = driver.title
            page_source = driver.page_source
            
            logger.info(f"    📋 URL actual: {current_url}")
            logger.info(f"    📋 Título: {page_title[:100]}...")
            logger.info(f"    📋 Tamaño HTML: {len(page_source)} caracteres")
            
            # Detectar problemas o bloqueos
            page_issues = detect_blocking_or_issues(driver, page_source, URL)
            
            if page_issues:
                logger.warning(f"    ⚠️ PROBLEMAS DETECTADOS:")
                for issue in page_issues:
                    logger.warning(f"      - {issue}")
                
                # Guardar muestra de la página problemática
                debug_file = save_page_debug(URL, page_source, i, "blocked")
                logger.warning(f"    🐛 Muestra guardada en: {debug_file}")
                all_issues.extend(page_issues)
            
            logger.info("    📊 Extrayendo datos...")
            df_page = scrape_page_source(page_source, logger)
            
            if not df_page.empty:
                save(df_page, logger)
                successful_pages += 1
                consecutive_failures = 0
                logger.info(f"    ✅ Éxito: {len(df_page)} propiedades extraídas")
            else:
                logger.warning("    ⚠️ No se encontraron propiedades en esta página")
                failed_pages += 1
                consecutive_failures += 1
                
                # Guardar muestra de página sin datos
                debug_file = save_page_debug(URL, page_source, i, "no_data")
                logger.warning(f"    🐛 Página sin datos - muestra guardada en: {debug_file}")
                
                # Si varias páginas consecutivas fallan, probablemente llegamos al final o hay bloqueo
                if consecutive_failures >= 5:
                    logger.error(f"    🚨 {consecutive_failures} páginas consecutivas sin datos - POSIBLE BLOQUEO")
                    logger.error("    🛑 Deteniendo scraping por seguridad")
                    break
                elif consecutive_failures >= 3:
                    logger.warning(f"    🔄 {consecutive_failures} páginas consecutivas sin datos - posible final")
            
        except Exception as e:
            logger.error(f"    ❌ Error al cargar la página: {e}")
            failed_pages += 1
            consecutive_failures += 1
            
            # Intentar obtener información del error
            try:
                error_page = driver.page_source
                error_file = save_page_debug(URL, error_page, i, "error")
                logger.error(f"    🐛 Página de error guardada en: {error_file}")
            except:
                logger.error("    ❌ No se pudo guardar información del error")
            
        finally:
            try:
                driver.quit()
            except:
                logger.warning("    ⚠️ Error al cerrar driver")
        
        # Guardar reporte de progreso
        issues_summary = {}
        for issue in all_issues:
            issue_type = issue.split(":")[0]
            issues_summary[issue_type] = issues_summary.get(issue_type, 0) + 1
        
        save_progress_report(i, successful_pages, failed_pages, issues_summary)
        
        # Pausa entre páginas como el script original
        sleep_time = random.uniform(3, 6)  # Pausas del script original
        logger.info(f"    😴 Pausa como original: {sleep_time:.1f}s...")
        time.sleep(sleep_time)
    
    # Reporte final
    logger.info(f"\n🎯 SCRAPING COMPLETADO:")
    logger.info(f"   ✅ Páginas exitosas: {successful_pages}")
    logger.info(f"   ❌ Páginas fallidas: {failed_pages}")
    logger.info(f"   📄 Total procesadas: {i}")
    logger.info(f"   📊 Tasa de éxito: {(successful_pages / i * 100):.1f}%")
    
    if all_issues:
        logger.warning(f"\n⚠️ RESUMEN DE PROBLEMAS DETECTADOS:")
        issue_counts = {}
        for issue in all_issues:
            issue_type = issue.split(":")[0]
            issue_counts[issue_type] = issue_counts.get(issue_type, 0) + 1
        
        for issue_type, count in issue_counts.items():
            logger.warning(f"   - {issue_type}: {count} veces")
    
    logger.info(f"\n📁 Archivos generados:")
    logger.info(f"   - Logs: {LOGS_DIR}")
    logger.info(f"   - Datos: {DATA_DIR}")
    logger.info(f"   - Muestras de páginas: {os.path.join(LOGS_DIR, 'page_samples')}")

if __name__ == "__main__":
    main()
