#!/usr/bin/env python3
"""
Lamudi Unico Professional Scraper - PropertyScraper Dell710
Scraper profesional para detalles de propiedades individuales de Lamudi
Optimizado para Dell T710 con capacidades de resilencia
"""

import os
import sys
import json
import time
import csv
import logging
import pickle
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import argparse

# Selenium imports
from seleniumbase import SB
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException

class LamudiUnicoProfessionalScraper:
    """
    Scraper profesional para detalles de propiedades individuales de lamudi.com.mx
    Segunda fase del proceso de scraping - procesa URLs individuales
    """
    
    def __init__(self, urls_file=None, headless=True, max_properties=None, resume_from=None, operation_type='venta'):
        self.urls_file = urls_file
        self.headless = headless
        self.max_properties = max_properties
        self.resume_from = resume_from or 0
        self.operation_type = operation_type
        
        # Configuración de paths
        self.setup_paths()
        
        # Configuración de logging
        self.setup_logging()
        
        # Checkpoint system
        self.checkpoint_file = self.checkpoint_dir / f"lamudi_unico_{operation_type}_checkpoint.pkl"
        self.checkpoint_interval = 25  # Guardar cada 25 propiedades procesadas
        
        # Cargar URLs
        self.property_urls = self.load_urls()
        self.properties_data = []
        
        # Performance metrics
        self.start_time = None
        self.properties_processed = 0
        self.successful_extractions = 0
        self.errors_count = 0
        
        self.logger.info(f"🚀 Iniciando Lamudi Unico Professional Scraper")
        self.logger.info(f"   URLs file: {urls_file}")
        self.logger.info(f"   Total URLs: {len(self.property_urls)}")
        self.logger.info(f"   Operation: {operation_type}")
        self.logger.info(f"   Max properties: {max_properties}")
        self.logger.info(f"   Resume from: {resume_from}")
        self.logger.info(f"   Headless: {headless}")
    
    def setup_paths(self):
        """Configurar estructura de paths del proyecto"""
        self.project_root = Path(__file__).parent.parent
        
        # Configuración de operaciones con abreviaciones
        operation_folders = {
            'venta': 'ven',
            'renta': 'ren'
        }
        operation_folder = operation_folders.get(self.operation_type, 'ven')
        
        # Obtener fecha actual en formato abreviado
        now = datetime.now()
        month_abbrev = self.get_month_abbreviation(now.month)
        year_short = str(now.year)[2:]  # Últimos 2 dígitos del año
        script_number = self.get_script_number(month_abbrev, year_short)
        
        # Nueva estructura: data/lam/{operation}/{mesAño}/{script}/
        self.data_dir = self.project_root / 'data' / 'lam' / operation_folder / f"{month_abbrev}{year_short}" / str(script_number)
        self.logs_dir = self.project_root / 'logs'
        self.checkpoint_dir = self.project_root / 'logs' / 'checkpoints'
        
        # Crear directorios si no existen
        for directory in [self.data_dir, self.logs_dir, self.checkpoint_dir]:
            directory.mkdir(parents=True, exist_ok=True)
    
    def get_month_abbreviation(self, month_num):
        """Obtener abreviatura de 3 letras del mes"""
        month_abbrevs = {
            1: 'ene', 2: 'feb', 3: 'mar', 4: 'abr', 5: 'may', 6: 'jun',
            7: 'jul', 8: 'ago', 9: 'sep', 10: 'oct', 11: 'nov', 12: 'dic'
        }
        return month_abbrevs.get(month_num, 'unk')
    
    def get_script_number(self, month_abbrev, year_short):
        """Detectar automáticamente el número de script basado en carpetas existentes"""
        # Construir la ruta base para este mes/año
        operation_folders = {'venta': 'ven', 'renta': 'ren'}
        operation_folder = operation_folders.get(self.operation_type, 'ven')
        base_path = self.project_root / 'data' / 'lam' / operation_folder / f"{month_abbrev}{year_short}"
        
        if not base_path.exists():
            return 1
        
        # Buscar carpetas numéricas existentes
        existing_scripts = []
        for item in base_path.iterdir():
            if item.is_dir() and item.name.isdigit():
                existing_scripts.append(int(item.name))
        
        return max(existing_scripts) + 1 if existing_scripts else 1
    
    def setup_logging(self):
        """Configurar sistema de logging profesional"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        log_file = self.logs_dir / f"lamudi_unico_{self.operation_type}_professional_{timestamp}.log"
        
        # Configuración de logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s | %(levelname)8s | %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S',
            handlers=[
                logging.FileHandler(log_file, encoding='utf-8'),
                logging.StreamHandler(sys.stdout)
            ]
        )
        
        self.logger = logging.getLogger(__name__)
        self.log_file = log_file
    
    def load_urls(self) -> List[str]:
        """Cargar URLs desde archivo"""
        urls = []
        
        if not self.urls_file:
            # Buscar el archivo más reciente de URLs con nueva nomenclatura
            pattern = f"LAM_URLs_*.csv"
            url_files = list(self.data_dir.glob(pattern))
            if url_files:
                self.urls_file = max(url_files, key=lambda x: x.stat().st_mtime)
                self.logger.info(f"📂 Usando archivo de URLs más reciente: {self.urls_file}")
            else:
                self.logger.error("❌ No se encontró archivo de URLs")
                return []
        
        try:
            with open(self.urls_file, 'r', encoding='utf-8') as f:
                urls = [line.strip() for line in f if line.strip()]
            self.logger.info(f"📂 Cargadas {len(urls)} URLs desde {self.urls_file}")
        except Exception as e:
            self.logger.error(f"❌ Error cargando URLs: {e}")
        
        return urls
    
    def create_professional_driver(self):
        """
        Crear driver optimizado para Dell T710 con técnicas anti-detección probadas
        """
        self.logger.info("🔧 Creando driver profesional optimizado...")
        
        # Configuración específica para Dell T710
        sb_config = {
            'uc': True,  # Modo undetectable para sitios sofisticados
            'headless': self.headless,
            'disable_dev_shm_usage': True,
            'disable_gpu': True,
            'disable_features': 'VizDisplayCompositor',
            'disable_extensions': True,
            'disable_plugins': True,
            'disable_images': False,
            'disable_javascript': False,
            'block_images': False,
            'maximize_window': not self.headless,
            'window_size': "1920,1080" if self.headless else None,
            'user_agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'locale_code': 'es-MX',
            'timeout': 30,
            'chromium_arg': [
                '--no-sandbox',  # Requerido para Ubuntu Server
                '--disable-dev-shm-usage',  # Evita problemas de memoria compartida
                '--disable-gpu',  # No usar GPU en headless
                '--disable-background-timer-throttling',
                '--disable-backgrounding-occluded-windows',
                '--disable-renderer-backgrounding',
                '--disable-extensions',
                '--disable-plugins',
                '--disable-sync',
                '--disable-translate',
                '--hide-scrollbars',
                '--mute-audio',
                '--no-first-run',
                '--safebrowsing-disable-auto-update',
                '--ignore-ssl-errors',
                '--ignore-certificate-errors',
                '--allow-running-insecure-content',
                '--disable-web-security',
                '--disable-features=VizDisplayCompositor',
            ]
        }
        
        return sb_config
    
    def load_checkpoint(self) -> Optional[Dict]:
        """Cargar checkpoint anterior si existe"""
        if self.checkpoint_file.exists():
            try:
                with open(self.checkpoint_file, 'rb') as f:
                    checkpoint = pickle.load(f)
                self.logger.info(f"📂 Checkpoint cargado: propiedad {checkpoint.get('last_index', 0)}")
                return checkpoint
            except Exception as e:
                self.logger.warning(f"⚠️  Error cargando checkpoint: {e}")
        return None
    
    def save_checkpoint(self, index: int):
        """Guardar checkpoint del progreso actual"""
        checkpoint = {
            'last_index': index,
            'properties_processed': self.properties_processed,
            'successful_extractions': self.successful_extractions,
            'timestamp': datetime.now().isoformat(),
            'operation_type': self.operation_type
        }
        
        try:
            with open(self.checkpoint_file, 'wb') as f:
                pickle.dump(checkpoint, f)
            self.logger.info(f"💾 Checkpoint guardado: índice {index}")
        except Exception as e:
            self.logger.error(f"❌ Error guardando checkpoint: {e}")
    
    def extract_detailed_property_data(self, sb, url: str) -> Optional[Dict]:
        """
        Extraer datos detallados de una propiedad individual
        """
        try:
            # Datos básicos
            property_data = {
                'timestamp': datetime.now().isoformat(),
                'operation_type': self.operation_type,
                'property_url': url
            }
            
            # Título principal
            try:
                title_selectors = [
                    "h1[data-testid='listing-title']",
                    "h1.listing-title",
                    "h1.property-title",
                    "h1"
                ]
                title = self.get_text_by_selectors(sb, title_selectors)
                property_data['titulo'] = title
            except:
                property_data['titulo'] = "N/A"
            
            # Precio
            try:
                price_selectors = [
                    "[data-testid='listing-price']",
                    ".listing-price",
                    ".property-price",
                    ".price"
                ]
                price = self.get_text_by_selectors(sb, price_selectors)
                property_data['precio'] = price
            except:
                property_data['precio'] = "N/A"
            
            # Ubicación detallada
            try:
                location_selectors = [
                    "[data-testid='listing-address']",
                    ".listing-address",
                    ".property-address",
                    ".address"
                ]
                location = self.get_text_by_selectors(sb, location_selectors)
                property_data['ubicacion_detallada'] = location
            except:
                property_data['ubicacion_detallada'] = "N/A"
            
            # Tipo de propiedad
            try:
                type_selectors = [
                    "[data-testid='property-type']",
                    ".property-type",
                    ".listing-type"
                ]
                prop_type = self.get_text_by_selectors(sb, type_selectors)
                property_data['tipo_propiedad'] = prop_type
            except:
                property_data['tipo_propiedad'] = "N/A"
            
            # Características principales (habitaciones, baños, área)
            try:
                features_selectors = [
                    "[data-testid='property-features']",
                    ".property-features",
                    ".listing-features"
                ]
                features_element = None
                for selector in features_selectors:
                    try:
                        features_element = sb.find_element(selector)
                        break
                    except:
                        continue
                
                if features_element:
                    # Extraer características específicas
                    feature_items = features_element.find_elements(By.CSS_SELECTOR, "li, .feature-item, .spec-item")
                    features = [item.text.strip() for item in feature_items if item.text.strip()]
                    property_data['caracteristicas_principales'] = " | ".join(features)
                else:
                    property_data['caracteristicas_principales'] = "N/A"
            except:
                property_data['caracteristicas_principales'] = "N/A"
            
            # Área/Superficie
            try:
                area_selectors = [
                    "[data-testid='property-area']",
                    ".property-area",
                    ".listing-area",
                    ".area"
                ]
                area = self.get_text_by_selectors(sb, area_selectors)
                property_data['area'] = area
            except:
                property_data['area'] = "N/A"
            
            # Descripción completa
            try:
                description_selectors = [
                    "[data-testid='property-description']",
                    ".property-description",
                    ".listing-description",
                    ".description"
                ]
                description = self.get_text_by_selectors(sb, description_selectors)
                property_data['descripcion_completa'] = description
            except:
                property_data['descripcion_completa'] = "N/A"
            
            # Amenidades/Servicios
            try:
                amenities_selectors = [
                    "[data-testid='property-amenities']",
                    ".property-amenities",
                    ".amenities",
                    ".services"
                ]
                amenities_element = None
                for selector in amenities_selectors:
                    try:
                        amenities_element = sb.find_element(selector)
                        break
                    except:
                        continue
                
                if amenities_element:
                    amenity_items = amenities_element.find_elements(By.CSS_SELECTOR, "li, .amenity-item")
                    amenities = [item.text.strip() for item in amenity_items if item.text.strip()]
                    property_data['amenidades'] = " | ".join(amenities)
                else:
                    property_data['amenidades'] = "N/A"
            except:
                property_data['amenidades'] = "N/A"
            
            # Información del agente/contacto
            try:
                agent_selectors = [
                    "[data-testid='agent-info']",
                    ".agent-info",
                    ".contact-info"
                ]
                agent = self.get_text_by_selectors(sb, agent_selectors)
                property_data['info_agente'] = agent
            except:
                property_data['info_agente'] = "N/A"
            
            # Verificar que se extrajo al menos información básica
            if property_data['titulo'] != "N/A" or property_data['precio'] != "N/A":
                return property_data
            else:
                self.logger.warning(f"⚠️  No se pudo extraer información básica de {url}")
                return None
                
        except Exception as e:
            self.logger.error(f"❌ Error extrayendo datos de {url}: {e}")
            return None
    
    def get_text_by_selectors(self, sb, selectors: List[str]) -> str:
        """Helper para probar múltiples selectores y retornar el primer texto encontrado"""
        for selector in selectors:
            try:
                element = sb.find_element(selector)
                text = element.text.strip()
                if text:
                    return text
            except:
                continue
        return "N/A"
    
    def wait_and_check_blocking(self, sb, timeout=15) -> bool:
        """
        Verificar si la página está bloqueada o cargada correctamente
        """
        try:
            # Esperar a que carguen elementos de la página de detalle
            WebDriverWait(sb.driver, timeout).until(
                lambda driver: (
                    driver.find_elements(By.CSS_SELECTOR, "h1") or
                    driver.find_elements(By.CSS_SELECTOR, ".listing-title") or
                    driver.find_elements(By.CSS_SELECTOR, "#challenge-form") or
                    driver.find_elements(By.CSS_SELECTOR, ".cf-browser-verification")
                )
            )
            
            # Verificar elementos de bloqueo
            blocking_selectors = [
                "#challenge-form",
                ".cf-browser-verification", 
                ".cf-checking-browser",
                "title:contains('Just a moment')",
                "h1:contains('Checking your browser')",
                ".captcha",
                "#captcha"
            ]
            
            for selector in blocking_selectors:
                if sb.is_element_visible(selector):
                    self.logger.warning(f"🚫 Página bloqueada - detectado: {selector}")
                    return False
            
            # Verificar si la página tiene contenido
            content_found = (
                sb.find_elements("h1") or
                sb.find_elements(".listing-title") or
                sb.find_elements(".property-title")
            )
            
            if content_found:
                self.logger.debug("✅ Página de detalle cargada correctamente")
                return True
            else:
                self.logger.warning("⚠️  Página cargada pero sin contenido detectado")
                return False
                
        except TimeoutException:
            self.logger.error("❌ Timeout esperando que cargue la página de detalle")
            return False
        except Exception as e:
            self.logger.error(f"❌ Error verificando bloqueo: {e}")
            return False
    
    def scrape_properties(self) -> Tuple[int, int]:
        """
        Método principal de scraping de propiedades individuales
        Retorna (total_processed, successful_extractions)
        """
        self.start_time = datetime.now()
        
        if not self.property_urls:
            self.logger.error("❌ No hay URLs para procesar")
            return 0, 0
        
        # Cargar checkpoint si existe
        checkpoint = self.load_checkpoint()
        if checkpoint and self.resume_from == 0:
            self.resume_from = checkpoint.get('last_index', 0)
            self.logger.info(f"🔄 Resumiendo desde índice {self.resume_from}")
        
        with SB(**self.create_professional_driver()) as sb:
            
            start_index = self.resume_from
            end_index = len(self.property_urls)
            
            if self.max_properties:
                end_index = min(start_index + self.max_properties, end_index)
            
            consecutive_failures = 0
            max_consecutive_failures = 10
            
            for i in range(start_index, end_index):
                url = self.property_urls[i]
                
                try:
                    self.logger.info(f"🏠 Procesando propiedad {i+1}/{len(self.property_urls)}: {url}")
                    
                    # Navegar a la página de la propiedad
                    sb.open(url)
                    
                    # Pausa para carga
                    time.sleep(3)
                    
                    # Verificar bloqueo y esperar carga
                    if not self.wait_and_check_blocking(sb):
                        consecutive_failures += 1
                        self.errors_count += 1
                        
                        if consecutive_failures >= max_consecutive_failures:
                            self.logger.error(f"❌ Demasiados fallos consecutivos ({consecutive_failures}). Deteniendo.")
                            break
                        
                        self.logger.warning(f"⚠️  Propiedad {i+1} falló. Continuando...")
                        time.sleep(5)
                        continue
                    
                    # Extraer datos de la propiedad
                    property_data = self.extract_detailed_property_data(sb, url)
                    
                    if property_data:
                        self.properties_data.append(property_data)
                        self.successful_extractions += 1
                        consecutive_failures = 0  # Reset contador
                        self.logger.info(f"✅ Datos extraídos exitosamente para propiedad {i+1}")
                    else:
                        consecutive_failures += 1
                        self.errors_count += 1
                        self.logger.warning(f"⚠️  No se pudieron extraer datos de propiedad {i+1}")
                    
                    self.properties_processed += 1
                    
                    # Guardar checkpoint cada N propiedades
                    if (i + 1) % self.checkpoint_interval == 0:
                        self.save_checkpoint(i)
                    
                    # Log de progreso
                    elapsed = datetime.now() - self.start_time
                    avg_time_per_property = elapsed.total_seconds() / self.properties_processed
                    success_rate = (self.successful_extractions / self.properties_processed) * 100
                    
                    self.logger.info(f"📊 Progreso - Procesadas: {self.properties_processed} | Exitosas: {self.successful_extractions} | Tasa éxito: {success_rate:.1f}% | Tiempo: {avg_time_per_property:.1f}s/prop")
                    
                    # Pausa entre propiedades (anti-detección)
                    time.sleep(2)
                    
                except KeyboardInterrupt:
                    self.logger.info("⏹️  Scraping interrumpido por usuario")
                    self.save_checkpoint(i)
                    break
                    
                except Exception as e:
                    consecutive_failures += 1
                    self.errors_count += 1
                    self.logger.error(f"❌ Error procesando propiedad {i+1}: {e}")
                    
                    if consecutive_failures >= max_consecutive_failures:
                        self.logger.error("❌ Demasiados errores consecutivos. Deteniendo.")
                        break
                    
                    time.sleep(5)
        
        return self.properties_processed, self.successful_extractions
    
    def save_results(self) -> str:
        """Guardar resultados en formato CSV con metadata"""
        if not self.properties_data:
            self.logger.warning("⚠️  No hay datos para guardar")
            return None

        # Generar timestamp para archivos
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        # Obtener fecha actual en formato abreviado para nombre de archivo
        now = datetime.now()
        month_abbrev = self.get_month_abbreviation(now.month)
        year_short = str(now.year)[2:]
        script_number = str(self.get_script_number(month_abbrev, year_short) - 1)  # -1 porque ya se creó la carpeta
        
        # Archivo CSV de detalles con nueva nomenclatura
        csv_filename = f"lam_det_{month_abbrev}{year_short}_{script_number}.csv"
        csv_path = self.data_dir / csv_filename
        
        # Guardar CSV
        with open(csv_path, 'w', newline='', encoding='utf-8') as csvfile:
            if self.properties_data:
                fieldnames = self.properties_data[0].keys()
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(self.properties_data)
        
        # Metadata
        metadata = {
            'execution_info': {
                'timestamp': timestamp,
                'operation_type': self.operation_type,
                'total_urls_provided': len(self.property_urls),
                'properties_processed': self.properties_processed,
                'successful_extractions': self.successful_extractions,
                'errors_count': self.errors_count,
                'execution_time_seconds': (datetime.now() - self.start_time).total_seconds(),
                'csv_filename': csv_filename,
                'log_filename': self.log_file.name,
                'urls_file_used': str(self.urls_file) if self.urls_file else None
            },
            'system_info': {
                'scraper_version': '1.0.0',
                'scraper_type': 'detailed_individual_properties',
                'python_version': sys.version,
                'headless_mode': self.headless,
                'max_properties_limit': self.max_properties,
                'resume_from_index': self.resume_from
            }
        }
        
        metadata_path = self.data_dir / f"metadata_unico_{timestamp}.json"
        with open(metadata_path, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, indent=2, ensure_ascii=False)
        
        self.logger.info(f"💾 Resultados guardados:")
        self.logger.info(f"   📄 CSV Detalles: {csv_path}")
        self.logger.info(f"   📋 Metadata: {metadata_path}")
        
        # Limpiar checkpoint al finalizar exitosamente
        if self.checkpoint_file.exists():
            self.checkpoint_file.unlink()
            self.logger.info("🗑️  Checkpoint limpiado")
        
        return str(csv_path)
    
    def run(self) -> Dict:
        """Ejecutar scraping completo y retornar resultados"""
        self.logger.info("🚀 Iniciando scraping detallado de propiedades Lamudi")
        self.logger.info("="*70)
        
        try:
            # Ejecutar scraping
            properties_processed, successful_extractions = self.scrape_properties()
            
            if properties_processed == 0:
                return {
                    'success': False,
                    'error': 'No se procesaron propiedades',
                    'properties_processed': 0,
                    'successful_extractions': 0
                }
            
            # Guardar resultados
            csv_path = self.save_results()
            
            # Calcular estadísticas finales
            total_time = datetime.now() - self.start_time
            avg_time_per_property = total_time.total_seconds() / max(properties_processed, 1)
            success_rate = (successful_extractions / max(properties_processed, 1)) * 100
            
            results = {
                'success': True,
                'properties_processed': properties_processed,
                'successful_extractions': successful_extractions,
                'errors_count': self.errors_count,
                'total_time_seconds': total_time.total_seconds(),
                'avg_time_per_property': avg_time_per_property,
                'success_rate': success_rate,
                'csv_file': csv_path,
                'operation_type': self.operation_type
            }
            
            # Log final
            self.logger.info("="*70)
            self.logger.info("🎉 SCRAPING DETALLADO COMPLETADO EXITOSAMENTE")
            self.logger.info(f"📊 Propiedades procesadas: {properties_processed}")
            self.logger.info(f"✅ Extracciones exitosas: {successful_extractions}")
            self.logger.info(f"❌ Errores: {self.errors_count}")
            self.logger.info(f"⏱️  Tiempo total: {total_time}")
            self.logger.info(f"⚡ Promedio por propiedad: {avg_time_per_property:.1f}s")
            self.logger.info(f"✅ Tasa de éxito: {success_rate:.1f}%")
            self.logger.info("="*70)
            
            return results
            
        except Exception as e:
            self.logger.error(f"❌ Error fatal en scraping: {e}")
            return {
                'success': False,
                'error': str(e),
                'properties_processed': self.properties_processed,
                'successful_extractions': self.successful_extractions
            }

def main():
    """Función principal con argumentos de línea de comandos"""
    parser = argparse.ArgumentParser(description='Lamudi Unico Professional Scraper')
    parser.add_argument('--urls-file', type=str, default=None,
                       help='Archivo con URLs de propiedades a procesar')
    parser.add_argument('--headless', action='store_true', default=True, 
                       help='Ejecutar en modo headless (sin GUI)')
    parser.add_argument('--properties', type=int, default=None, 
                       help='Número máximo de propiedades a procesar')
    parser.add_argument('--resume', type=int, default=0, 
                       help='Índice desde el cual resumir')
    parser.add_argument('--operation', choices=['venta', 'renta'], default='venta',
                       help='Tipo de operación: venta o renta')
    parser.add_argument('--gui', action='store_true', 
                       help='Ejecutar con GUI (opuesto a --headless)')
    
    args = parser.parse_args()
    
    # Ajustar headless basado en argumentos
    if args.gui:
        args.headless = False
    
    # Crear y ejecutar scraper
    scraper = LamudiUnicoProfessionalScraper(
        urls_file=args.urls_file,
        headless=args.headless,
        max_properties=args.properties,
        resume_from=args.resume,
        operation_type=args.operation
    )
    
    results = scraper.run()
    
    # Retornar código de salida apropiado
    sys.exit(0 if results['success'] else 1)

if __name__ == "__main__":
    main()
