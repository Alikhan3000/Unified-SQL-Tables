# database_setup.py
import sqlite3
import os
from typing import List, Dict

class DatabaseSetup:
    def __init__(self, db_path: str = "./data/company_data.db"):
        self.db_path = db_path
        self.ensure_data_directory()
        
    def ensure_data_directory(self):
        """Create data directory if it doesn't exist"""
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
    
    def create_tables(self):
        """Create all necessary tables"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Users table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            department TEXT,
            city TEXT,
            join_date DATE,
            salary REAL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        ''')
        
        # Products table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            category TEXT,
            price REAL,
            stock_quantity INTEGER,
            description TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        ''')
        
        # Sales table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS sales (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            product_id INTEGER,
            quantity INTEGER,
            total_amount REAL,
            sale_date DATE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id),
            FOREIGN KEY (product_id) REFERENCES products (id)
        )
        ''')
        
        conn.commit()
        conn.close()
        print("✅ Database tables created successfully")
    
    def insert_sample_data(self):
        """Insert sample data for testing"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Sample users
        users_data = [
            ('John Doe', 'john@company.com', 'Engineering', 'New York', '2023-01-15', 85000),
            ('Jane Smith', 'jane@company.com', 'Marketing', 'Los Angeles', '2023-02-20', 75000),
            ('Mike Johnson', 'mike@company.com', 'Sales', 'Chicago', '2023-03-10', 65000),
            ('Sarah Wilson', 'sarah@company.com', 'Engineering', 'Seattle', '2023-01-30', 90000),
        ]
        
        # Insert users
        for user in users_data:
            cursor.execute("INSERT INTO users (name, email, department, city, join_date, salary) VALUES (?, ?, ?, ?, ?, ?)", user)
        
        # Sample products
        products_data = [
            ('iPhone 14', 'Electronics', 999.99, 50, 'Latest iPhone model'),
            ('MacBook Pro', 'Electronics', 1999.99, 25, 'High-performance laptop'),
            ('Nike Air Force 1', 'Apparel', 99.99, 100, 'Classic sneaker'),
            ('Amazon Echo Dot', 'Electronics', 49.99, 75, 'Smart home device'),
        ]
        
        # Insert products
        for product in products
