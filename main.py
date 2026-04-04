from database_handler import DatabaseHandler
import requests
import os
from dotenv import load_dotenv

load_dotenv()

class HealthcareChatbot:
    def __init__(self):
        self.name = "🏥 HealthDataBot"
        self.db = DatabaseHandler()
        self.ollama_url = os.getenv('OLLAMA_HOST')
        self.model = os.getenv('OLLAMA_MODEL')
        print(f"Hello! I'm {self.name}")
        print("🔥 Connected to your 6,850-row healthcare database!")
        print("💡 Type 'help', 'dashboard', or ask about patients/labs/etc.\n")
    
    def ask_ollama(self, prompt):
        """Ask Ollama to generate SQL"""
        try:
            response = requests.post(f"{self.ollama_url}/api/generate", json={
                "model": self.model,
                "prompt": prompt,
                "stream": False
            }, timeout=30)
            if response.status_code == 200:
                return response.json()['response'].strip()
        except:
            pass
        return None
    
    def format_results(self, data, question):
        """Make results doctor-friendly"""
        if not data:
            return "✅ No matching records found"
        
        total = len(data)
        
        # Patient-focused formatting
        if any(table in question.lower() for table in ['patient', 'demographic']):
            names = []
            for row in data[:5]:
                name = f"{row.get('first_name', 'N/A')} {row.get('last_name', 'N/A')}"
                city = row.get('city', 'N/A')
                names.append(f"• {name} ({city})")
            return f"✅ Found {total} patients:\n" + "\n".join(names)
        
        # Lab results
        elif 'lab' in question.lower():
            labs = []
            for row in data[:5]:
                test = row.get('test_name', 'Unknown')
                result = row.get('result_value', 'N/A')
                flag = row.get('abnormal_flag', '')
                flag_emoji = "🔴" if flag in ['High', 'Low', 'Critical'] else "🟢"
                labs.append(f"• {test}: {result} {flag_emoji}")
            return f"✅ Found {total} lab results:\n" + "\n".join(labs)
        
        # Medications
        elif 'medication' in question.lower() or 'pharmacy' in question.lower():
            meds = []
            for row in data[:5]:
                med = row.get('medication_name', 'Unknown')
                dosage = row.get('dosage', 'N/A')
                meds.append(f"• {med} ({dosage})")
            return f"✅ Found {total} medications:\n" + "\n".join(meds)
        
        # Default pretty table
        else:
            preview = []
            for row in data[:3]:
                row_str = ", ".join([f"{k}: {v}" for k, v in list(row.items())[:3]])
                preview.append(row_str)
            return f"✅ Found {total} records:\n" + "\n".join(preview)
    
    def get_response(self, user_input):
        user_input = user_input.strip()
        
        if user_input.lower() in ['quit', 'exit', 'bye']:
            return None
        
        # Quick dashboard
        if any(word in user_input.lower() for word in ['dashboard', 'stats', 'overview', 'summary']):
            stats = self.db.execute_query("""
                SELECT 
                    (SELECT COUNT(*) FROM patient_demographics) as total_patients,
                    (SELECT COUNT(*) FROM ehr_encounter) as total_encounters,
                    (SELECT COUNT(*) FROM lab_result WHERE abnormal_flag != 'Normal') as abnormal_labs,
                    (SELECT COUNT(*) FROM pharmacy_medication) as total_meds,
                    (SELECT COUNT(*) FROM claims_encounter WHERE claim_status = 'Paid') as paid_claims
            """)
            if stats['success']:
                row = stats['data'][0]
                return f"""🏥 HEALTHCARE DASHBOARD:
• 👥 {row['total_patients']:,} Total Patients
• 🏥 {row['total_encounters']:,} Encounters
• 🧪 {row['abnormal_labs']:,} Abnormal Labs
• 💊 {row['total_meds']:,} Medications
• 💰 {row['paid_claims']:,} Paid Claims"""
        
        if 'help' in user_input.lower():
            return """🏥 ASK ME ABOUT YOUR DATA:

📊 **Quick Stats:** "dashboard" | "stats" | "overview"

👥 **Patients:** 
• "New York patients" | "recent patients" | "patients by city"

🧪 **Labs:** 
• "recent lab results" | "abnormal labs" | "diabetes labs"

💊 **Medications:** 
• "diabetes medications" | "recent prescriptions"

🏥 **Encounters:** 
• "recent encounters" | "telehealth visits"

💰 **Claims:** 
• "recent claims" | "paid claims" | "denied claims"

📱 **Devices:** 
• "recent device readings" | "heart rate data"

Type 'quit' to exit
"""
        
        # Get schema
        schema = self.db.get_schema()
        schema_text = "\n".join([f"{row[0]}.{row[1]} ({row[2]})" for row in schema[:50]])  # Limit schema size
        
        # Better SQL prompt for healthcare
        sql_prompt = f"""You are a healthcare data analyst writing MySQL for doctors.

UNIFIED DATABASE (8 tables, all linked by patient_id):
patient_demographics ← patient_socioeconomic, remote_device_reading, ehr_encounter, claims_encounter
ehr_encounter ← lab_result, pharmacy_medication, procedure_record

Key columns:
- patient_demographics: patient_id, first_name, last_name, city, date_of_birth
- lab_result: test_name, result_value, abnormal_flag, result_time
- pharmacy_medication: medication_name, dosage
- ehr_encounter: encounter_type, encounter_start
- claims_encounter: claim_status, paid_amount

Question: "{user_input}"

Write ONE clean SELECT query with LIMIT 10. Use proper JOINs. Return ONLY SQL:
"""
        
        print("🤔 Analyzing...")
        sql_query = self.ask_ollama(sql_prompt)
        
        if not sql_query:
            return "❌ Ollama timeout. Try a simpler question."
        
        print(f"📊 SQL: {sql_query}")
        
        # Run query
        result = self.db.execute_query(sql_query)
        
        if "error" in result:
            return f"❌ Query error: {result['error']}\n💡 Try: 'dashboard' or 'help'"
        
        # Format beautifully
        return self.format_results(result['data'], user_input)
    
    def start_chat(self):
        while True:
            try:
                user_input = input("\nYou: ").strip()
                response = self.get_response(user_input)
                if response is None:
                    print("👋 Thanks for using HealthDataBot!")
                    break
                print(f"\n{self.name}: {response}\n")
            except KeyboardInterrupt:
                print("\n👋 Goodbye!")
                break

if __name__ == "__main__":
    chatbot = HealthcareChatbot()
    chatbot.start_chat()