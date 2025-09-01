"""
URL utilities for scrapers
"""

import csv
from pathlib import Path
from typing import List, Dict

def load_urls_from_csv(csv_path: str) -> List[Dict]:
    """
    Carga URLs desde un archivo CSV
    """
    urls = []
    csv_file = Path(csv_path)
    
    if not csv_file.exists():
        print(f"Warning: CSV file {csv_path} not found")
        return urls
    
    try:
        with open(csv_file, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                urls.append(row)
    except Exception as e:
        print(f"Error reading CSV {csv_path}: {e}")
    
    return urls

def extract_url_column(row: Dict, url_columns=['url', 'URL', 'link', 'Link']) -> str:
    """
    Extrae la URL de una fila del CSV
    """
    for col in url_columns:
        if col in row and row[col]:
            return row[col].strip()
    
    # Si no encuentra una columna específica, devuelve el primer valor
    values = list(row.values())
    return values[0] if values else ""
