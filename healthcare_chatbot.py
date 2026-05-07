from database_handler import DatabaseHandler
from milvus_handler import MilvusHandler
import requests
import os
from dotenv import load_dotenv
from datetime import datetime
from rapidfuzz import fuzz

load_dotenv()


class HealthcareChatbot:
    def __init__(self):
        self.name = "🏥 HealthDataBot Pro"
        self.db = DatabaseHandler()
        self.milvus = None
        self.ollama_url = os.getenv("OLLAMA_HOST", "http://localhost:11434")
        self.model = os.getenv("OLLAMA_MODEL", "llama3.2")

        print(f"🚀 Initializing {self.name}...")
        print("✅ Connected to MySQL unified database!")
        self.print_table_stats()

        try:
            self.milvus = MilvusHandler()
            print("🧠 Connected to Milvus")
        except Exception as e:
            print(f"⚠️ Milvus unavailable, semantic search disabled: {e}")
            self.milvus = None

        print("💡 Ready for SQL + semantic search! Type 'help' to start\n")

    def fuzzy_contains_intent(self, user_input, phrases, threshold=80):
        text = (user_input or "").lower().strip()

        for phrase in phrases:
            phrase = phrase.lower().strip()

            if phrase in text:
                return True

            score1 = fuzz.partial_ratio(text, phrase)
            score2 = fuzz.token_set_ratio(text, phrase)
            score3 = fuzz.partial_token_ratio(text, phrase)

            if max(score1, score2, score3) >= threshold:
                return True

        return False

    def is_note_query(self, user_input: str) -> bool:
        text = (user_input or "").lower().strip()

        note_keywords = [
            "note", "notes", "clinical", "chart", "record", "history",
            "symptom", "symptoms", "complaint", "complaints",
            "assessment", "plan", "soap", "hpi"
        ]

        symptom_keywords = [
            "chest pain", "shortness of breath", "chest pressure", "chest tightness",
            "diabetes", "hypertension", "hypotension", "fever", "cough",
            "headache", "dizziness", "nausea", "vomiting", "fatigue",
            "wheezing", "palpitations", "edema", "dyspnea"
        ]

        if any(k in text for k in note_keywords):
            return True

        if any(k in text for k in symptom_keywords):
            return True

        return self.fuzzy_contains_intent(text, note_keywords + symptom_keywords, threshold=75)

    def ask_ollama(self, prompt, timeout=90):
        try:
            response = requests.post(
                f"{self.ollama_url}/api/generate",
                json={
                    "model": self.model,
                    "prompt": prompt,
                    "stream": False,
                    "options": {
                        "temperature": 0.1,
                        "top_p": 0.9
                    }
                },
                timeout=timeout
            )
            if response.status_code == 200:
                return response.json()["response"].strip()
        except requests.exceptions.Timeout:
            return None
        except Exception as e:
            print(f"❌ Ollama error: {e}")
            return None
        return None

    def print_table_stats(self):
        print("📋 Checking tables:")

        expected_tables = [
            "patient_demographics",
            "patient_socioeconomic",
            "remote_device_reading",
            "ehr_encounter",
            "lab_result",
            "pharmacy_medication",
            "procedure_record",
            "claims_encounter",
        ]

        try:
            # Try to get actual table names from the database if available
            try:
                db_table_names = self.db.get_table_names() or []
            except Exception:
                db_table_names = []

            # Build an ordered list: keep expected first (if present), then append any extra DB tables
            if db_table_names:
                ordered = [t for t in expected_tables if t in db_table_names]
                extras = [t for t in db_table_names if t not in ordered]
                tables_to_check = ordered + extras
            else:
                tables_to_check = expected_tables

            for table in tables_to_check:
                try:
                    count = self.db.get_row_count(table)
                    if isinstance(count, int) and count >= 0:
                        print(f"   ✅ {table}: {count:,} rows")
                    else:
                        print(f"   ⚠️ {table}: unavailable")
                except Exception:
                    print(f"   ⚠️ {table}: unavailable")

        except Exception as e:
            print(f"⚠️ Could not retrieve table stats: {e}")

    def semantic_search_notes(self, query, limit=5):
        if not self.milvus:
            return None

        try:
            print(f"🧠 Semantic search: {query}")
            results = self.milvus.search_notes(query, limit=limit)

            if not results:
                return None

            output = f"🧠 **{len(results)} similar clinical notes for:** `{query}`\n\n"
            for i, r in enumerate(results, 1):
                patient_id = r.get("patient_id", "N/A")
                encounter_type = r.get("encounter_type", "Unknown")
                encounter_start = r.get("encounter_start", "N/A")
                chief_complaint = r.get("chief_complaint", "N/A")
                distance = r.get("distance", 0.0)

                preview = (r.get("note_text", "") or "").replace("\n", " ").strip()
                if len(preview) > 200:
                    preview = preview[:200] + "..."

                output += f"{i}. **Pt {patient_id}** | {encounter_type} | {encounter_start}\n"
                output += f"   🩺 {chief_complaint}\n"
                output += f"   📊 Distance: {distance:.3f}\n"
                output += f"   💬 {preview}\n\n"

            return output
        except Exception as e:
            print(f"⚠️ Milvus search failed: {e}")
            return None

    def build_note_token_query(self, user_input, limit=5):
        text = (user_input or "").lower().strip()

        stopwords = {
            "note", "notes", "clinical", "chart", "record", "records",
            "show", "find", "search", "for", "with", "about", "the",
            "a", "an", "and", "or", "of", "patient", "patients"
        }

        tokens = [t.strip() for t in text.replace(",", " ").split()]
        tokens = [t for t in tokens if len(t) > 2 and t not in stopwords]

        if not tokens:
            tokens = [text]

        safe_tokens = [t.replace("'", "''") for t in tokens]

        where_parts = []
        score_parts = []

        for token in safe_tokens:
            where_parts.append(
                f"(LOWER(COALESCE(notes, '')) LIKE '%{token}%' OR LOWER(COALESCE(chief_complaint, '')) LIKE '%{token}%')"
            )
            score_parts.append(
                f"(CASE WHEN LOWER(COALESCE(notes, '')) LIKE '%{token}%' "
                f"OR LOWER(COALESCE(chief_complaint, '')) LIKE '%{token}%' "
                f"THEN 1 ELSE 0 END)"
            )

        where_clause = " AND ".join(where_parts)
        score_clause = " + ".join(score_parts)

        query = f"""
        SELECT
            patient_id,
            encounter_id,
            chief_complaint,
            notes,
            ({score_clause}) AS relevance_score,
            LENGTH(COALESCE(notes, '')) AS note_length
        FROM ehr_encounter
        WHERE {where_clause}
        ORDER BY relevance_score DESC, note_length DESC, encounter_id DESC
        LIMIT {limit}
        """
        return query

    def keyword_note_search(self, user_input, limit=5):
        try:
            print(f"🔍 Keyword note fallback: {user_input}")
            query = self.build_note_token_query(user_input, limit=limit)
            result = self.db.execute_query(query)

            if "error" in result:
                return f"❌ Keyword note search failed: {result['error'][:120]}"

            rows = result.get("data", [])
            if not rows:
                return f"✅ No clinical notes found for '{user_input}'"

            output = f"📝 **{len(rows)} clinical note matches for:** `{user_input}`\n\n"
            for i, row in enumerate(rows, 1):
                preview = (row.get("notes") or row.get("chief_complaint", "") or "").replace("\n", " ").strip()
                if len(preview) > 220:
                    preview = preview[:220] + "..."

                output += f"{i}. **Pt {row.get('patient_id', 'N/A')}** | Encounter {row.get('encounter_id', 'N/A')}\n"
                output += f"   🩺 {row.get('chief_complaint', 'N/A')}\n"
                output += f"   💬 {preview}\n\n"

            return output
        except Exception as e:
            return f"❌ Keyword note search exception: {str(e)}"

    def semantic_search_with_fallback(self, user_input, limit=5):
        print(f"🧭 Note query route: {user_input}")

        milvus_result = self.semantic_search_notes(user_input, limit=limit)
        if milvus_result:
            return milvus_result

        print("📝 Falling back to keyword note search...")
        return self.keyword_note_search(user_input, limit=limit)

    def classify_intent_llm(self, user_input):
        prompt = f"""
Classify this healthcare chatbot request into exactly ONE label from: help, dashboard, semantic, sql, hybrid

Rules:
- help = asking what bot can do (help, ?, what can you do)
- dashboard = wants stats/summary (dashboard, stats, overview, summary)
- semantic = clinical notes, symptoms, diagnoses (notes, chest pain, diabetes, symptoms)
- sql = structured data (labs, patients, medications, claims, devices)
- hybrid = both clinical notes AND structured data

Query: "{user_input}"

Respond with ONLY one word: help/dashboard/semantic/sql/hybrid
"""
        result = self.ask_ollama(prompt, timeout=15)
        if result and result.strip().lower() in ["help", "dashboard", "semantic", "sql", "hybrid"]:
            return result.strip().lower()
        return "sql"

    def hybrid_search_response(self, user_input):
        note_output = self.semantic_search_with_fallback(user_input, limit=3)

        sql_rows = []
        sql_prompt = f"""
Generate ONE MySQL SELECT query for: "{user_input}"

Tables:
- patient_demographics
- ehr_encounter
- lab_result
- pharmacy_medication
- claims_encounter
- procedure_record
- remote_device_reading

Use LIMIT 10.
Return ONLY SQL.
"""
        sql_query = self.ask_ollama(sql_prompt)

        if sql_query and sql_query.strip().upper().startswith("SELECT"):
            result = self.db.execute_query(sql_query)
            if "error" not in result:
                sql_rows = result.get("data", [])

        output = f"🔍 **Hybrid results for:** `{user_input}`\n\n"

        if note_output and not note_output.startswith("✅ No clinical notes found"):
            output += note_output + "\n"
        else:
            output += "🧠 No semantic note matches found\n\n"

        if sql_rows:
            output += f"📊 **Structured data ({len(sql_rows)}):**\n"
            for row in sql_rows[:3]:
                preview = ", ".join([f"{k}={v}" for k, v in list(row.items())[:4]])
                output += f"• {preview}\n"
        else:
            output += "📊 No structured data found\n"

        return output

    def format_results(self, data, question):
        if not data:
            return "✅ No matching records found"

        total = len(data)
        question_lower = question.lower()

        if any(word in question_lower for word in ["patient", "demo", "name", "age", "city"]):
            patients = []
            for row in data[:8]:
                name = f"{row.get('first_name', '')} {row.get('last_name', '')}".strip()
                age = self.calculate_age(row.get("date_of_birth"))
                city = row.get("city", "N/A")
                patients.append(f"• {name or 'N/A'}, {age}yo ({city})")
            return f"👥 **{total} patients:**\n" + "\n".join(patients)

        elif "lab" in question_lower:
            labs = []
            for row in data[:10]:
                test = row.get("test_name", "Unknown")
                result = row.get("result_value", row.get("result_numeric", "N/A"))
                flag = row.get("abnormal_flag", "Normal")
                emoji = {"High": "🔴", "Low": "🔴", "Critical": "🔴", "Borderline": "🟡"}.get(flag, "🟢")
                labs.append(f"• {test}: {result} {emoji}")
            return f"🧪 **{total} labs:**\n" + "\n".join(labs)

        elif any(word in question_lower for word in ["med", "pharm", "rx"]):
            meds = []
            for row in data[:8]:
                med = row.get("medication_name", "Unknown")
                dosage = row.get("dosage", "N/A")
                meds.append(f"• {med} ({dosage})")
            return f"💊 **{total} medications:**\n" + "\n".join(meds)

        elif any(word in question_lower for word in ["encounter", "visit", "proc"]):
            visits = []
            for row in data[:8]:
                type_ = row.get("chief_complaint") or row.get("procedure_description", "Visit")
                visits.append(f"• {str(type_)[:50]}...")
            return f"🏥 **{total} encounters/procedures:**\n" + "\n".join(visits)

        else:
            preview = []
            for row in data[:5]:
                row_str = ", ".join([f"{k}={v}" for k, v in list(row.items())[:4]])
                preview.append(row_str)
            return f"📋 **{total} records:**\n" + "\n".join(preview)

    def calculate_age(self, dob_str):
        if not dob_str or dob_str == "N/A":
            return "N/A"
        try:
            if isinstance(dob_str, str):
                dob = datetime.strptime(dob_str[:10], "%Y-%m-%d")
            else:
                dob = dob_str
            today = datetime.now()
            age = today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))
            return str(age)
        except Exception:
            return "N/A"

    def get_help(self):
        return """🏥 **HealthDataBot Pro** - Smart Healthcare AI

**🚀 QUICK START:**
• `chest pain notes`
• `dashboard`
• `help`
• `quit`

**🧠 NOTE SEARCH:**
• "chest pain notes"
• "diabetes complications"
• "hypertension management"

**📊 STRUCTURED DATA:**
• "abnormal A1C labs"
• "metformin patients"
• "unpaid claims"
• "heart rate alerts"
"""

    def get_dashboard(self):
        stats_query = """
        SELECT
            (SELECT COUNT(*) FROM patient_demographics) AS total_patients,
            (SELECT COUNT(*) FROM ehr_encounter) AS total_encounters,
            (SELECT COUNT(*)
             FROM lab_result
             WHERE abnormal_flag IS NOT NULL
               AND TRIM(abnormal_flag) <> ''
               AND UPPER(abnormal_flag) <> 'NORMAL') AS abnormal_labs,
            (SELECT COUNT(*) FROM pharmacy_medication) AS total_meds,
            (SELECT COUNT(*) FROM claims_encounter WHERE UPPER(claim_status) = 'PAID') AS paid_claims,
            (SELECT COUNT(*)
             FROM remote_device_reading
             WHERE LOWER(COALESCE(measurement_type, '')) LIKE '%heart%'
                OR LOWER(COALESCE(measurement_type, '')) LIKE '%hr%') AS heart_rate_readings,
            (SELECT COUNT(*) FROM procedure_record) AS total_procedures
        """
        result = self.db.execute_query(stats_query)
        if "error" in result or not result.get("data"):
            return "❌ Dashboard unavailable"

        row = result["data"][0]
        milvus_status = "✅ connected" if self.milvus else "⚠️ disabled"

        return f"""🏥 **DASHBOARD** ({datetime.now().strftime('%H:%M')})

👥 **Patients:** {row['total_patients']:,}
🏥 **Encounters:** {row['total_encounters']:,}
🧪 **Abnormal Labs:** {row['abnormal_labs']:,} 🔴
💊 **Medications:** {row['total_meds']:,}
💰 **Paid Claims:** {row.get('paid_claims', 0):,}
📱 **Heart Rate:** {row.get('heart_rate_readings', 0):,}
🔪 **Procedures:** {row.get('total_procedures', 0):,}

🧠 **Milvus:** {milvus_status}
"""

    def generate_sql_response(self, user_input):
        schema = self.db.get_schema()
        schema_text = "\n".join([f"{row[0]}.{row[1]}" for row in schema[:25]])

        sql_prompt = f"""Healthcare SQL expert. Write ONE SELECT query.

SCHEMA:
{schema_text}

Question: "{user_input}"
LIMIT 10.
Return ONLY valid SQL.
"""
        print("🤔 Generating SQL...")
        sql_query = self.ask_ollama(sql_prompt)

        if not sql_query or not sql_query.strip().upper().startswith("SELECT"):
            return "❌ SQL generation failed. Try 'dashboard' or 'help'"

        print(f"📊 Executing: {sql_query[:100]}...")
        result = self.db.execute_query(sql_query)

        if "error" in result:
            return f"❌ Query failed: {result['error'][:120]}..."

        return self.format_results(result.get("data", []), user_input)

    def get_response(self, user_input):
        user_input_lower = (user_input or "").lower().strip()
        print(f"🔍 Processing: '{user_input}'")

        if user_input_lower in ["quit", "exit", "bye", "q"]:
            return None

        if user_input_lower in ["help", "h", "?"]:
            return self.get_help()

        if self.fuzzy_contains_intent(user_input, ["dashboard", "stats", "overview"], 85):
            print("📊 Dashboard detected")
            return self.get_dashboard()

        note_patterns = [
            "note", "notes", "clinical", "chart", "record", "history", "hpi",
            "symptom", "symptoms", "complaint", "complaints", "soap", "assessment",
            "chest pain", "chest pressure", "chest tightness", "shortness of breath",
            "diabetes", "hypertension", "hypotension", "fever", "cough", "headache",
            "dizziness", "nausea", "vomiting", "fatigue", "wheezing", "palpitation",
            "edema", "dyspnea", "sob", "cp", "mi", "hf", "copd", "pna",
            "covid", "flu", "pneumonia", "asthma", "cad", "afib", "vtach",
            "brady", "chf", "esrd", "cirrhosis", "sepsis"
        ]

        if any(pattern in user_input_lower for pattern in note_patterns):
            print("🧠 Note query detected")

            sql_markers = ["lab", "labs", "med", "rx", "patient", "claim", "device"]
            wants_sql = any(marker in user_input_lower for marker in sql_markers)

            if wants_sql:
                print("🔍 Hybrid request")
                return self.hybrid_search_response(user_input)

            return self.semantic_search_with_fallback(user_input)

        sql_markers = ["lab", "labs", "medication", "meds", "rx", "patient", "claim", "encounter", "device"]
        if any(marker in user_input_lower for marker in sql_markers):
            print("📊 SQL query detected")
            return self.generate_sql_response(user_input)

        intent = self.classify_intent_llm(user_input)
        print(f"🤖 LLM intent: {intent}")

        if intent == "semantic":
            return self.semantic_search_with_fallback(user_input)
        if intent == "hybrid":
            return self.hybrid_search_response(user_input)
        if intent == "dashboard":
            return self.get_dashboard()

        return self.generate_sql_response(user_input)

    def start_chat(self):
        print("🎯 HealthDataBot Pro ready!\n")

        while True:
            try:
                user_input = input("\nYou: ").strip()
                if not user_input:
                    continue

                response = self.get_response(user_input)
                if response is None:
                    print("\n👋 Thanks for using HealthDataBot Pro!")
                    break

                print(f"\n{self.name}\n{response}\n")

            except KeyboardInterrupt:
                print("\n\n👋 Goodbye!")
                break
            except Exception as e:
                print(f"❌ Error: {e}")


if __name__ == "__main__":
    chatbot = HealthcareChatbot()
    chatbot.start_chat()