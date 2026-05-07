#!/usr/bin/env python3
"""
Export the database schema to db_schema.json.
Run: python export_schema.py
"""
import os
import json
from pathlib import Path
import mysql.connector
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / '.env')

def get_connection():
    return mysql.connector.connect(
        host=os.getenv('MYSQL_HOST','localhost'),
        port=int(os.getenv('MYSQL_PORT',3306)),
        user=os.getenv('MYSQL_USER','root'),
        password=os.getenv('MYSQL_PASSWORD','root'),
        database=os.getenv('MYSQL_DATABASE')
    )

def export_schema(out_path: Path):
    conn = get_connection()
    cursor = conn.cursor()
    db = os.getenv('MYSQL_DATABASE')
    query = '''
    SELECT TABLE_NAME, COLUMN_NAME, DATA_TYPE
    FROM INFORMATION_SCHEMA.COLUMNS
    WHERE TABLE_SCHEMA = %s
    ORDER BY TABLE_NAME, ORDINAL_POSITION
    '''
    cursor.execute(query, (db,))
    rows = cursor.fetchall()
    schema = {}
    for table, column, dtype in rows:
        schema.setdefault(table, {})[column] = dtype

    out = {
        'generated_at': None,
        'notes': 'Auto-exported schema. Add example rows manually if desired.',
        'tables': {}
    }
    for t, cols in schema.items():
        out['tables'][t] = {'columns': cols, 'example': {}}

    with open(out_path, 'w', encoding='utf-8') as f:
        json.dump(out, f, indent=2, ensure_ascii=False)

    cursor.close()
    conn.close()
    print(f'Wrote schema to {out_path}')

if __name__ == '__main__':
    export_schema(BASE_DIR / 'db_schema.json')
