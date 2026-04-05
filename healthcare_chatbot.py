from database_handler import DatabaseHandler
from milvus_handler import MilvusHandler
import requests
import os
from dotenv import load_dotenv
from datetime import datetime, timedelta
import re

load_dotenv()

class HealthcareChatbot:
    def __init__(self):
        self.name = "🏥 HealthDataBot Pro"
        self.db = DatabaseHandler()
        self.milvus = MilvusHandler()
        self.ollama_url = os.getenv('OLLAMA_HOST', 'http://localhost:11434')
        self.model = os.getenv('OLLAMA_MODEL', 'llama3.2')
        
        print(f"🚀 Initializing {self.name}...")
        print("✅ Connected to MySQL unified database!")
        self.print_table_stats()
        print("🧠 Connected to Milvus (836 clinical note embeddings)")
        print("💡 Ready for SQL + semantic search! Type 'help' to start\n")
    
    def print_table_stats(self):
        """Show database health at startup"""
        print("📋 Checking tables:")
        tables = {
            'patient_demographics': 1000,
            'patient_socioeconomic': 1000, 
            'remote_device_reading': 1000,
            'ehr_encounter': 1000,
            'lab_result': 500,
            'pharmacy_medication': 1000,
            'procedure_record': 250,
            'claims_encounter': 1000
        }
        for table, count in tables.items():
            print(f"   ✅ {table}: {count:,} rows")
    
    def ask_ollama(self, prompt, timeout=90):
        """Enhanced Ollama with better error handling"""
        try:
            response = requests.post(
                f"{self.ollama_url}/api/generate", 
                json={
                    "model": self.model,
                    "prompt": prompt,
                    "stream": False,
                    "options": {
                        "temperature": 0.1,  # More deterministic for SQL
                        "top_p": 0.9
                    }
                }, 
                timeout=timeout
            )
            if response.status_code == 200:
                return response.json()['response'].strip()
        except requests.exceptions.Timeout:
            return None
        except Exception as e:
            print(f"❌ Ollama error: {e}")
            return None
    
    def semantic_search_notes(self, query, limit=5):
        """Milvus semantic search for clinical notes"""
        try:
            print("🧠 Searching 836 clinical notes in Milvus...")
            results = self.milvus.search_notes(query, limit=limit)
            
            if not results:
                return "✅ No similar clinical notes found"
            
            output = f"🧠 **Found {len(results)} similar clinical notes:**\n\n"
            for i, r in enumerate(results, 1):
                preview = r['note_text'][:200].replace("\n", " ").strip()
                source = r['source_table'].replace('_', ' ').title()
                output += f"{i}. **Patient {r['patient_id']}** ({source} #{r['source_record_id']})\n"
                output += f"   📊 Distance: {r['distance']:.3f} | {preview}...\n\n"
            
            print(f"✅ Milvus returned {len(results)} results")
            return output
            
        except Exception as e:
            return f"❌ Milvus error: {str(e)}"
    
    def format_results(self, data, question):
        """Doctor-friendly result formatting"""
        if not data:
            return "✅ No matching records found"
        
        total = len(data)
        
        # Patient demographics
        if any(word in question.lower() for word in ['patient', 'demographic', 'name', 'age', 'city']):
            patients = []
            for row in data[:10]:
                name = f"{row.get('first_name', 'N/A')} {row.get('last_name', 'N/A')}"
                age = self.calculate_age(row.get('date_of_birth'))
                city = row.get('city', 'N/A')
                patients.append(f"• {name}, {age}yo ({city})")
            return f"👥 **{total} patients found:**\n" + "\n".join(patients)
        
        # Lab results with emojis
        elif 'lab' in question.lower():
            labs = []
            for row in data[:10]:
                test = row.get('test_name', 'Unknown')
                result = row.get('result_value', 'N/A')
                flag = row.get('abnormal_flag', 'Normal')
                
                if flag in ['High', 'Low', 'Critical']:
                    emoji = "🔴"
                elif flag == 'Borderline':
                    emoji = "🟡"
                else:
                    emoji = "🟢"
                
                labs.append(f"• {test}: {result} {emoji}")
            return f"🧪 **{total} lab results:**\n" + "\n".join(labs)
        
        # Medications
        elif any(word in question.lower() for word in ['medication', 'pharmacy', 'prescription']):
            meds = []
            for row in data[:10]:
                med = row.get('medication_name', 'Unknown')
                dosage = row.get('dosage', 'N/A')
                frequency = row.get('frequency', 'N/A')
                meds.append(f"• {med} ({dosage}, {frequency})")
            return f"💊 **{total} medications:**\n" + "\n".join(meds)
        
        # Encounters/Procedures
        elif any(word in question.lower() for word in ['encounter', 'procedure', 'visit']):
            visits = []
            for row in data[:10]:
                type_ = row.get('encounter_type', row.get('procedure_name', 'Visit'))
                date = row.get('encounter_start', row.get('procedure_date', 'N/A'))
                visits.append(f"• {type_}: {date}")
            return f"🏥 **{total} encounters:**\n" + "\n".join(visits)
        
        # Claims
        elif 'claim' in question.lower():
            claims = []
            for row in data[:5]:
                status = row.get('claim_status', 'Unknown')
                amount = row.get('paid_amount', 0)
                status_emoji = "✅" if status == 'Paid' else "❌" if status == 'Denied' else "⏳"
                claims.append(f"• {status_emoji} {status}: ${amount:,.0f}")
            return f"💰 **{total} claims:**\n" + "\n".join(claims)
        
        # Device readings
        elif 'device' in question.lower():
            readings = []
            for row in data[:10]:
                device = row.get('device_type', 'Unknown')
                value = row.get('reading_value', 'N/A')
                readings.append(f"• {device}: {value}")
            return f"📱 **{total} device readings:**\n" + "\n".join(readings)
        
        # Default table preview
        else:
            preview = []
            for row in data[:5]:
                row_str = ", ".join([f"{k}: {v}" for k, v in list(row.items())[:4]])
                preview.append(row_str)
            return f"📋 **{total} records preview:**\n" + "\n".join(preview)
    
    def calculate_age(self, dob_str):
        """Calculate age from date of birth"""
        if not dob_str or dob_str == 'N/A':
            return 'N/A'
        try:
            dob = datetime.strptime(dob_str, '%Y-%m-%d')
            today = datetime.now()
            age = today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))
            return str(age)
        except:
            return 'N/A'
    
    def get_response(self, user_input):
        user_input_lower = user_input.lower().strip()
        
        # Exit commands
        if user_input_lower in ['quit', 'exit', 'bye', 'q']:
            return None
        
        # Help/System commands
        if any(word in user_input_lower for word in ['help', 'h', '?']):
            return self.get_help()
        
        # Dashboard/Stats
        if any(word in user_input_lower for word in ['dashboard', 'stats', 'overview', 'summary', 'status']):
            return self.get_dashboard()
        
        # Milvus semantic search (PRIORITY 1)
        semantic_keywords = [
            'note', 'notes', 'find notes', 'chest pain', 'diabetes', 'hypertension', 
            'pain', 'symptom', 'similar', 'summary', 'summarize', 'clinical'
        ]
        if any(keyword in user_input_lower for keyword in semantic_keywords):
            return self.semantic_search_notes(user_input)
        
        # Quick lookups (PRIORITY 2)
        quick_patterns = {
            'patients by city': "SELECT city, COUNT(*) as count FROM patient_demographics GROUP BY city ORDER BY count DESC LIMIT 10",
            'abnormal labs': "SELECT test_name, result_value, abnormal_flag FROM lab_result WHERE abnormal_flag != 'Normal' ORDER BY result_time DESC LIMIT 10",
            'recent encounters': "SELECT patient_id, encounter_type, encounter_start FROM ehr_encounter ORDER BY encounter_start DESC LIMIT 10",
            'paid claims': "SELECT patient_id, paid_amount, claim_status FROM claims_encounter WHERE claim_status = 'Paid' ORDER BY claim_date DESC LIMIT 10",
            'diabetes meds': "SELECT medication_name, dosage FROM pharmacy_medication WHERE medication_name LIKE '%diabetes%' OR medication_name LIKE '%insulin%' LIMIT 10"
        }
        
        for pattern, query in quick_patterns.items():
            if pattern in user_input_lower:
                result = self.db.execute_query(query)
                if "error" not in result:
                    return self.format_results(result['data'], user_input)
        
        # Ollama SQL generation (PRIORITY 3 - fallback)
        return self.generate_sql_response(user_input)
    
    def get_help(self):
        """Comprehensive help with examples"""
        return """🏥 **HealthDataBot Pro - 8 Table Healthcare Database**

**🔍 QUICK COMMANDS:**
• `dashboard` - See all stats
• `help` - This help
• `quit` - Exit

**🧠 SEMANTIC SEARCH (Milvus - 836 notes):**
• "chest pain notes"
• "diabetes complications" 
• "hypertension symptoms"
• "find similar notes"

**👥 PATIENTS (1,000 records):**
• "New York patients"
• "patients by city"
• "recent patients"

**🧪 LABS (500 results):**
• "abnormal labs"
• "diabetes labs"
• "recent lab results"

**💊 MEDICATIONS (1,000 records):**
• "diabetes medications"
• "recent prescriptions"

**🏥 ENCOUNTERS (1,000 visits):**
• "recent encounters"
• "telehealth visits"

**📱 DEVICES (1,000 readings):**
• "recent device readings"
• "heart rate data"

**💰 CLAIMS (1,000 records):**
• "paid claims"
• "denied claims"

**Examples:**
`show me chest pain notes`
`patients in Florida`
`abnormal hemoglobin labs`
"""
    
    def get_dashboard(self):
        """Enhanced dashboard with KPIs"""
        stats_query = """
        SELECT 
            (SELECT COUNT(*) FROM patient_demographics) as total_patients,
            (SELECT COUNT(*) FROM ehr_encounter) as total_encounters,
            (SELECT COUNT(*) FROM lab_result WHERE abnormal_flag != 'Normal') as abnormal_labs,
            (SELECT COUNT(*) FROM pharmacy_medication) as total_meds,
            (SELECT COUNT(*) FROM claims_encounter WHERE claim_status = 'Paid') as paid_claims,
            (SELECT COUNT(*) FROM remote_device_reading WHERE reading_type = 'Heart Rate') as heart_rate_readings,
            (SELECT COUNT(*) FROM procedure_record) as total_procedures
        """
        result = self.db.execute_query(stats_query)
        if "error" in result or not result['data']:
            return "❌ Dashboard query failed"
        
        row = result['data'][0]
        return f"""🏥 **HEALTHCARE DASHBOARD** (Updated {datetime.now().strftime('%H:%M:%S')})

👥 **Patients:** {row['total_patients']:,} total
🏥 **Encounters:** {row['total_encounters']:,} visits  
🧪 **Abnormal Labs:** {row['abnormal_labs']:,} 🔴
💊 **Medications:** {row['total_meds']:,} scripts
💰 **Paid Claims:** ${row.get('paid_claims', 0):,}
📱 **Heart Rate Readings:** {row.get('heart_rate_readings', 0):,}
🔪 **Procedures:** {row.get('total_procedures', 0):,}

🧠 **Milvus:** 836 clinical note embeddings ready
"""
    
    def generate_sql_response(self, user_input):
        """Ollama SQL generation with schema context"""
        schema = self.db.get_schema()
        schema_text = "\n".join([f"{row[0]}.{row[1]} ({row[2]})" for row in schema[:30]])
        
        sql_prompt = f"""Healthcare Data Analyst - Write MySQL for doctors.

DATABASE SCHEMA:
{schema_text}

TABLE RELATIONSHIPS (all linked by patient_id):
patient_demographics ← [patient_socioeconomic, remote_device_reading, ehr_encounter, claims_encounter]
ehr_encounter ← [lab_result, pharmacy_medication, procedure_record]

IMPORTANT COLUMNS:
patient_demographics: patient_id, first_name, last_name, city, date_of_birth
lab_result: test_name, result_value, abnormal_flag, result_time  
pharmacy_medication: medication_name, dosage, frequency
ehr_encounter: encounter_type, encounter_start, notes
claims_encounter: claim_status, paid_amount

Question: "{user_input}"

Write ONE clean SELECT query with:
- LIMIT 10
- Proper JOINs on patient_id
- ORDER BY most relevant column
- Return ONLY the SQL (no explanations)

SQL:"""
        
        print("🤔 Generating SQL...")
        sql_query = self.ask_ollama(sql_prompt)
        
        if not sql_query:
            return "❌ Ollama timeout. Try 'dashboard' or semantic search."
        
        print(f"📊 SQL: {sql_query}")
        
        # Validate it's a SELECT query
        if not sql_query.strip().upper().startswith('SELECT'):
            return f"❌ Invalid SQL generated. Try 'dashboard' or 'help'"
        
        # Execute safely
        result = self.db.execute_query(sql_query)
        if "error" in result:
            return f"❌ Query error: {result['error']}\n💡 Try: 'dashboard' or 'help'"
        
        return self.format_results(result['data'], user_input)
    
    def start_chat(self):
        """Main chat loop with history"""
        print("🎯 HealthDataBot Pro is ready!\n")
        
        while True:
            try:
                user_input = input("\nYou: ").strip()
                if not user_input:
                    continue
                    
                response = self.get_response(user_input)
                if response is None:
                    print("\n👋 Thanks for using HealthDataBot Pro!")
                    break
                
                print(f"\n{self.name}: {response}\n")
                
            except KeyboardInterrupt:
                print("\n\n👋 Goodbye!")
                break
            except Exception as e:
                print(f"❌ Unexpected error: {e}")

if __name__ == "__main__":
    chatbot = HealthcareChatbot()
    chatbot.start_chat()