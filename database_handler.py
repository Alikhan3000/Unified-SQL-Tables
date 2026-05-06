import os
from typing import Any, Dict, List, Optional
import mysql.connector
from mysql.connector import Error
from dotenv import load_dotenv
from pathlib import Path

# FIXED: Explicit .env path + override
BASE_DIR = Path(__file__).parent
load_dotenv(dotenv_path=BASE_DIR / ".env", override=True)

class DatabaseHandler:
    def __init__(self):
        self.connection = None
        self.config = {
            "host": os.getenv("MYSQL_HOST", "localhost"),
            "port": int(os.getenv("MYSQL_PORT", "3306")),
            # FIXED: Use correct ENV vars with defaults
            "user": os.getenv("MYSQL_USER", "root"),
            "password": os.getenv("MYSQL_PASSWORD", "root"),
            "database": os.getenv("MYSQL_DATABASE", "unified"),
            "autocommit": True,
        }
        self.connect()

    # ... rest of your methods stay exactly the same ...

    def connect(self) -> bool:
        """Connect to the MySQL unified database."""
        try:
            missing = [k for k, v in self.config.items() if k in ["user", "password", "database"] and not v]
            if missing:
                print(f"❌ Missing required .env values: {', '.join(missing)}")
                print("💡 Expected: MYSQL_HOST, MYSQL_PORT, MYSQL_USER, MYSQL_PASSWORD, MYSQL_DATABASE")
                return False

            if self.connection and self.connection.is_connected():
                return True

            self.connection = mysql.connector.connect(**self.config)

            if self.connection.is_connected():
                db_name = self.config["database"]
                print(f"✅ Connected to MySQL unified database: {db_name}")
                self.test_tables()
                return True

            return False

        except Error as e:
            print(f"❌ MySQL connection failed: {e}")
            print("💡 Check your .env file and make sure MySQL is running")
            self.connection = None
            return False

    def ensure_connection(self) -> bool:
        """Reconnect if connection dropped."""
        try:
            if self.connection is None:
                return self.connect()

            self.connection.ping(reconnect=True, attempts=2, delay=1)
            return self.connection.is_connected()

        except Exception:
            self.connection = None
            return self.connect()

    def close(self):
        """Close MySQL connection safely."""
        try:
            if self.connection and self.connection.is_connected():
                self.connection.close()
                print("🔌 MySQL connection closed")
        except Exception:
            pass

    def test_tables(self):
        """Test all expected healthcare tables."""
        tables = [
            "patient_demographics",
            "patient_socioeconomic",
            "remote_device_reading",
            "ehr_encounter",
            "lab_result",
            "pharmacy_medication",
            "procedure_record",
            "claims_encounter",
        ]

        if not self.ensure_connection():
            print("❌ Cannot test tables: no database connection")
            return

        cursor = None
        try:
            cursor = self.connection.cursor()
            print("📋 Checking tables:")
            for table in tables:
                try:
                    cursor.execute(f"SELECT COUNT(*) FROM {table}")
                    count = cursor.fetchone()[0]
                    print(f"   ✅ {table}: {count:,} rows")
                except Error as e:
                    print(f"   ❌ {table}: unavailable ({e})")
        finally:
            if cursor:
                cursor.close()

    def execute_query(self, query: str, params: Optional[tuple] = None) -> Dict[str, Any]:
        """Run SELECT query safely."""
        if not query or not query.strip():
            return {"error": "Empty query"}

        normalized = query.strip().upper()
        if not normalized.startswith("SELECT"):
            return {"error": "Only SELECT queries allowed 😇"}

        if not self.ensure_connection():
            return {"error": "Database connection unavailable"}

        cursor = None
        try:
            cursor = self.connection.cursor(dictionary=True)
            cursor.execute(query, params or ())
            results = cursor.fetchall()
            print(f"✅ Query returned {len(results)} rows")
            return {"success": True, "data": results}

        except Error as e:
            return {"error": f"Query failed: {str(e)}"}

        finally:
            if cursor:
                cursor.close()

    def get_schema(self) -> List[tuple]:
        """Get table structure for LLM prompts."""
        if not self.ensure_connection():
            return []

        cursor = None
        try:
            cursor = self.connection.cursor()
            cursor.execute(
                """
                SELECT TABLE_NAME, COLUMN_NAME, DATA_TYPE, COLUMN_KEY, IS_NULLABLE
                FROM INFORMATION_SCHEMA.COLUMNS
                WHERE TABLE_SCHEMA = %s
                ORDER BY TABLE_NAME, ORDINAL_POSITION
                """,
                (self.config["database"],),
            )
            return cursor.fetchall()

        except Error as e:
            print(f"❌ Failed to load schema: {e}")
            return []

        finally:
            if cursor:
                cursor.close()

    def get_table_names(self) -> List[str]:
        """Return all table names in the active database."""
        if not self.ensure_connection():
            return []

        cursor = None
        try:
            cursor = self.connection.cursor()
            cursor.execute(
                """
                SELECT TABLE_NAME
                FROM INFORMATION_SCHEMA.TABLES
                WHERE TABLE_SCHEMA = %s
                ORDER BY TABLE_NAME
                """,
                (self.config["database"],),
            )
            return [row[0] for row in cursor.fetchall()]

        except Error as e:
            print(f"❌ Failed to get table names: {e}")
            return []

        finally:
            if cursor:
                cursor.close()

    def get_notes_for_embedding(self) -> List[Dict[str, Any]]:
        """Get notes from MySQL for Milvus embedding."""
        if not self.ensure_connection():
            return []

        query = """
        SELECT
            e.patient_id,
            e.encounter_id AS source_record_id,
            'ehr_encounter' AS source_table,
            e.notes AS note_text,
            e.encounter_type,
            e.encounter_start,
            e.chief_complaint
        FROM ehr_encounter e
        WHERE e.notes IS NOT NULL AND TRIM(e.notes) <> ''

        UNION ALL

        SELECT
            p.patient_id,
            p.procedure_id AS source_record_id,
            'procedure_record' AS source_table,
            p.notes AS note_text,
            p.procedure_name AS encounter_type,
            p.procedure_date AS encounter_start,
            NULL AS chief_complaint
        FROM procedure_record p
        WHERE p.notes IS NOT NULL AND TRIM(p.notes) <> ''
        """

        cursor = None
        try:
            cursor = self.connection.cursor(dictionary=True)
            cursor.execute(query)
            results = cursor.fetchall()
            print(f"🧠 Found {len(results)} notes for embedding")
            return results

        except Error as e:
            print(f"❌ Failed to fetch notes for embedding: {e}")
            return []

        finally:
            if cursor:
                cursor.close()

    def get_row_count(self, table_name: str) -> int:
        """Get row count for one table."""
        if not self.ensure_connection():
            return 0

        cursor = None
        try:
            cursor = self.connection.cursor()
            cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
            return cursor.fetchone()[0]

        except Error:
            return 0

        finally:
            if cursor:
                cursor.close()

    def health_check(self) -> Dict[str, Any]:
        """Simple DB health check."""
        ok = self.ensure_connection()
        return {
            "connected": ok,
            "database": self.config.get("database"),
            "host": self.config.get("host"),
            "port": self.config.get("port"),
        }


if __name__ == "__main__":
    db = DatabaseHandler()

    print("\n--- HEALTH CHECK ---")
    print(db.health_check())

    print("\n--- TABLES ---")
    print(db.get_table_names())

    print("\n--- SCHEMA PREVIEW ---")
    schema = db.get_schema()
    for row in schema[:10]:
        print(row)

    print("\n--- NOTES PREVIEW ---")
    notes = db.get_notes_for_embedding()
    print(f"Total notes: {len(notes)}")
    if notes:
        print(notes[0])

    db.close()