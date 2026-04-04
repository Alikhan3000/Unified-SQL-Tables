import mysql.connector
from mysql.connector import Error
from dotenv import load_dotenv
import os

load_dotenv()

class DatabaseHandler:
    def __init__(self):
        self.connection = None
        self.connect()
    
    def connect(self):
        """Connect to your MySQL unified database"""
        try:
            self.connection = mysql.connector.connect(
                host=os.getenv('MYSQL_HOST'),
                port=int(os.getenv('MYSQL_PORT')),
                user=os.getenv('MYSQL_USER'),
                password=os.getenv('MYSQL_PASSWORD'),
                database=os.getenv('MYSQL_DATABASE')
            )
            if self.connection.is_connected():
                print("✅ Connected to MySQL unified database!")
                self.test_tables()
                return True
        except Error as e:
            print(f"❌ MySQL connection failed: {e}")
            print("💡 Check your .env file username/password")
            return False
    
    def test_tables(self):
        """Test all 8 healthcare tables"""
        tables = [
            "patient_demographics", "patient_socioeconomic", "remote_device_reading",
            "ehr_encounter", "lab_result", "pharmacy_medication", 
            "procedure_record", "claims_encounter"
        ]
        cursor = self.connection.cursor()
        print("📋 Checking tables:")
        for table in tables:
            try:
                cursor.execute(f"SELECT COUNT(*) as cnt FROM {table}")
                count = cursor.fetchone()[0]
                print(f"   ✅ {table}: {count} rows")
            except:
                print(f"   ❌ {table}: missing or empty")
        cursor.close()
    
    def execute_query(self, query):
        """Run SELECT query safely"""
        if not query.strip().upper().startswith('SELECT'):
            return {"error": "Only SELECT queries allowed 😇"}
        
        try:
            cursor = self.connection.cursor(dictionary=True)
            cursor.execute(query)
            results = cursor.fetchall()
            cursor.close()
            print(f"✅ Query returned {len(results)} rows")
            return {"success": True, "data": results}
        except Error as e:
            return {"error": f"Query failed: {str(e)}"}
    
    def get_schema(self):
        """Get table structure for LLM"""
        cursor = self.connection.cursor()
        cursor.execute("""
            SELECT TABLE_NAME, COLUMN_NAME, DATA_TYPE, COLUMN_KEY, IS_NULLABLE
            FROM INFORMATION_SCHEMA.COLUMNS 
            WHERE TABLE_SCHEMA = 'unified'
            ORDER BY TABLE_NAME, ORDINAL_POSITION
        """)
        schema = cursor.fetchall()
        cursor.close()
        return schema
    
    def get_notes_for_embedding(self):
        """Get notes from MySQL for Milvus embedding"""
        query = """
        SELECT 
            patient_id,
            encounter_id AS source_record_id,
            'ehr_encounter' AS source_table,
            notes AS note_text
        FROM ehr_encounter
        WHERE notes IS NOT NULL AND TRIM(notes) != ''

        UNION ALL

        SELECT
            patient_id,
            procedure_id AS source_record_id,
            'procedure_record' AS source_table,
            notes AS note_text
        FROM procedure_record
        WHERE notes IS NOT NULL AND TRIM(notes) != ''
        """
        cursor = self.connection.cursor(dictionary=True)
        cursor.execute(query)
        results = cursor.fetchall()
        cursor.close()
        print(f"Found {len(results)} notes for embedding")
        return results