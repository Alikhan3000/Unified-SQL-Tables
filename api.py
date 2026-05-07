from flask import Flask, jsonify, request, session
from flask_cors import CORS
import mysql.connector
from mysql.connector import Error
from dotenv import load_dotenv
import os
import re
from pathlib import Path
import requests
import json


BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")

app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY", "dev-secret-key-change-me")

CORS(app, resources={
    r"/api/*": {
        # Allow local development origins and simple static file usage.
        # For local dev it's simpler to allow all origins; tighten this for production.
        "origins": "*",
        "methods": ["GET", "POST", "OPTIONS"],
        "allow_headers": ["Content-Type"]
    }
}, supports_credentials=True)


def get_connection():
    return mysql.connector.connect(
        host=os.getenv("MYSQL_HOST", "localhost"),
        port=int(os.getenv("MYSQL_PORT", 3306)),
        user=os.getenv("MYSQL_USER", "root"),
        password=os.getenv("MYSQL_PASSWORD", "root"),
        database=os.getenv("MYSQL_DATABASE", "unified")
    )

# Load cached DB schema if available
SCHEMA_PATH = BASE_DIR / "db_schema.json"
DB_SCHEMA = {}
def load_db_schema():
    global DB_SCHEMA
    try:
        if SCHEMA_PATH.exists():
            with open(SCHEMA_PATH, 'r', encoding='utf-8') as f:
                DB_SCHEMA = json.load(f).get('tables', {})
        else:
            DB_SCHEMA = {}
    except Exception:
        DB_SCHEMA = {}

load_db_schema()

def get_schema_snippet_for_query(query: str, max_chars: int = 800) -> str:
    """Return a short text snippet of relevant tables/columns for the LLM prompt."""
    if not DB_SCHEMA:
        return ""

    q = (query or "").lower()
    # Choose tables whose name or column names appear in the query
    matches = []
    for table, meta in DB_SCHEMA.items():
        table_low = table.lower()
        cols = list(meta.get('columns', {}).keys())
        cols_join = ' '.join(cols).lower()
        score = 0
        if table_low in q:
            score += 2
        for c in cols:
            if c.lower() in q:
                score += 1
        if score > 0:
            matches.append((score, table, cols))

    # Sort by score desc
    matches.sort(key=lambda x: -x[0])

    # If no matches, pick the top 3 tables by column count
    if not matches:
        picks = sorted(((len(meta.get('columns', {})), t, list(meta.get('columns', {}).keys())) for t, meta in DB_SCHEMA.items()), reverse=True)[:3]
        matches = [(0, t, cols) for cnt, t, cols in picks]

    # Build snippet
    parts = []
    for _, table, cols in matches:
        parts.append(f"{table}: {', '.join(cols[:8])}")
        if sum(len(p) for p in parts) > max_chars:
            break

    snippet = '\n'.join(parts)
    if len(snippet) > max_chars:
        snippet = snippet[:max_chars]
    return snippet

def validate_llm_results(results):
    """Ensure results are a list of dicts with required fields, sanitize types."""
    if not isinstance(results, list):
        return None
    out = []
    for item in results:
        if not isinstance(item, dict):
            continue
        title = item.get('title') or item.get('label') or item.get('patient_name')
        desc = item.get('description') or item.get('note_text') or ''
        if not title or not desc:
            continue
        score = item.get('score')
        try:
            score = float(score) if score is not None else None
        except Exception:
            score = None
        out.append({
            'title': str(title),
            'description': str(desc),
            'meta': item.get('meta') or '',
            'score': score or 0.0,
            'patient_id': item.get('patient_id')
        })
    return out if out else None


def simplify_query_for_db(q: str) -> str:
    """Turn a natural-language query into a compact DB-friendly search string."""
    if not q:
        return q
    q = q.lower()
    stopwords = set(["the","a","an","with","for","in","on","at","to","of","and","or","patients","patient","show","find","list","where","who","have","has","is","are"]) 
    tokens = [t.strip() for t in re.split(r"\W+", q) if t.strip()]
    tokens = [t for t in tokens if len(t) > 2 and t not in stopwords]
    if not tokens:
        return q
    # If a common multiword phrase exists, keep it (e.g., 'chest pain')
    joined = ' '.join(tokens)
    # Prefer keeping adjacent tokens that were phrases in original query
    # Simple heuristic: look for 'chest pain' or 'shortness breath'
    phrases = ["chest pain", "shortness of breath", "shortness breath", "high blood pressure", "heart rate"]
    for p in phrases:
        if p in q:
            return p
    return joined


def safe_int(value, default=0):
    try:
        return int(value)
    except Exception:
        return default


def classify_intent(message: str) -> str:
    msg = (message or "").lower().strip()

    if any(x in msg for x in [
        "stats", "summary", "dashboard", "kpi",
        "how many patients", "total patients", "high risk",
        "overview", "numbers"
    ]):
        return "stats"

    if any(x in msg for x in [
        "list patients", "show patients", "patient list",
        "recent patients", "all patients"
    ]):
        return "patients"

    if any(x in msg for x in [
        "help", "what can you do", "commands", "options"
    ]):
        return "help"

    if any(x in msg for x in [
        "that patient", "this patient", "previous patient",
        "last patient", "his labs", "her labs", "their meds",
        "show more", "more details"
    ]):
        return "followup"

    if any(x in msg for x in [
        "search", "find", "look up", "lookup",
        "abnormal", "glucose", "a1c", "hemoglobin", "cholesterol",
        "labs", "medications", "claims", "procedure", "device",
        "note", "encounter", "payer", "status"
    ]):
        return "search"

    return "general_search"


def extract_limit(message: str, default=10, max_limit=50):
    if not message:
        return default
    m = re.search(r"\b(\d{1,3})\b", message)
    if not m:
        return default
    n = safe_int(m.group(1), default)
    return min(max(n, 1), max_limit)


def extract_patient_name(message: str):
    if not message:
        return None

    patterns = [
        r"(?:patient\s+)([A-Z][a-z]+(?:\s+[A-Z][a-z]+)+)",
        r"(?:for\s+)([A-Z][a-z]+(?:\s+[A-Z][a-z]+)+)",
        r"(?:about\s+)([A-Z][a-z]+(?:\s+[A-Z][a-z]+)+)",
        r"(?:show\s+)([A-Z][a-z]+(?:\s+[A-Z][a-z]+)+)",
        r"(?:find\s+)([A-Z][a-z]+(?:\s+[A-Z][a-z]+)+)"
    ]

    for pattern in patterns:
        m = re.search(pattern, message)
        if m:
            return m.group(1).strip()

    return None


def fetch_stats_data():
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("SELECT COUNT(*) AS total_patients FROM patient_demographics")
    total_patients = cursor.fetchone()["total_patients"]

    cursor.execute("""
        SELECT COUNT(*) AS abnormal_labs
        FROM lab_result
        WHERE abnormal_flag IS NOT NULL
          AND TRIM(abnormal_flag) <> ''
          AND UPPER(abnormal_flag) <> 'NORMAL'
    """)
    abnormal_labs = cursor.fetchone()["abnormal_labs"]

    cursor.execute("SELECT COUNT(*) AS total_encounters FROM ehr_encounter")
    total_encounters = cursor.fetchone()["total_encounters"]

    cursor.execute("""
        SELECT COUNT(DISTINCT patient_id) AS high_risk_patients
        FROM (
            SELECT patient_id
            FROM lab_result
            WHERE abnormal_flag IS NOT NULL
              AND TRIM(abnormal_flag) <> ''
              AND UPPER(abnormal_flag) <> 'NORMAL'

            UNION ALL

            SELECT patient_id
            FROM remote_device_reading
            WHERE data_quality_flag IS NOT NULL
              AND UPPER(data_quality_flag) <> 'GOOD'
        ) x
    """)
    high_risk_patients = cursor.fetchone()["high_risk_patients"]

    cursor.close()
    conn.close()

    return {
        "total_patients": total_patients,
        "abnormal_labs": abnormal_labs,
        "total_encounters": total_encounters,
        "high_risk_patients": high_risk_patients
    }


def fetch_patient_list(limit=10):
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    query = """
    SELECT
        p.patient_id,
        CONCAT(COALESCE(p.first_name, ''), ' ', COALESCE(p.last_name, '')) AS patient_name,
        p.date_of_birth,
        TIMESTAMPDIFF(YEAR, p.date_of_birth, CURDATE()) AS age,
        p.city,
        p.state_province,
        COALESCE(ec.encounter_count, 0) AS encounter_count,
        COALESCE(lc.abnormal_lab_count, 0) AS abnormal_lab_count,
        COALESCE(mc.medication_count, 0) AS medication_count,
        COALESCE(rc.device_alert_count, 0) AS device_alert_count
    FROM patient_demographics p
    LEFT JOIN (
        SELECT patient_id, COUNT(*) AS encounter_count
        FROM ehr_encounter
        GROUP BY patient_id
    ) ec ON p.patient_id = ec.patient_id
    LEFT JOIN (
        SELECT patient_id, COUNT(*) AS abnormal_lab_count
        FROM lab_result
        WHERE abnormal_flag IS NOT NULL
          AND TRIM(abnormal_flag) <> ''
          AND UPPER(abnormal_flag) <> 'NORMAL'
        GROUP BY patient_id
    ) lc ON p.patient_id = lc.patient_id
    LEFT JOIN (
        SELECT patient_id, COUNT(*) AS medication_count
        FROM pharmacy_medication
        GROUP BY patient_id
    ) mc ON p.patient_id = mc.patient_id
    LEFT JOIN (
        SELECT patient_id, COUNT(*) AS device_alert_count
        FROM remote_device_reading
        WHERE data_quality_flag IS NOT NULL
          AND UPPER(data_quality_flag) <> 'GOOD'
        GROUP BY patient_id
    ) rc ON p.patient_id = rc.patient_id
    ORDER BY p.patient_id DESC
    LIMIT %s
    """

    cursor.execute(query, (limit,))
    rows = cursor.fetchall()

    cursor.close()
    conn.close()
    return rows


def find_patient_by_name(name: str):
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    like_name = f"%{name}%"
    parts = name.strip().split()

    query = """
    SELECT
        patient_id,
        CONCAT(COALESCE(first_name, ''), ' ', COALESCE(last_name, '')) AS patient_name,
        date_of_birth,
        TIMESTAMPDIFF(YEAR, date_of_birth, CURDATE()) AS age,
        city,
        state_province
    FROM patient_demographics
    WHERE CONCAT(COALESCE(first_name, ''), ' ', COALESCE(last_name, '')) LIKE %s
    ORDER BY patient_id DESC
    LIMIT 1
    """
    cursor.execute(query, (like_name,))
    row = cursor.fetchone()

    if not row and len(parts) >= 2:
        cursor.execute("""
            SELECT
                patient_id,
                CONCAT(COALESCE(first_name, ''), ' ', COALESCE(last_name, '')) AS patient_name,
                date_of_birth,
                TIMESTAMPDIFF(YEAR, date_of_birth, CURDATE()) AS age,
                city,
                state_province
            FROM patient_demographics
            WHERE first_name LIKE %s
              AND last_name LIKE %s
            ORDER BY patient_id DESC
            LIMIT 1
        """, (f"%{parts[0]}%", f"%{parts[-1]}%"))
        row = cursor.fetchone()

    cursor.close()
    conn.close()
    return row


def get_patient_summary(patient_id):
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("""
        SELECT
            p.patient_id,
            CONCAT(COALESCE(p.first_name, ''), ' ', COALESCE(p.last_name, '')) AS patient_name,
            p.date_of_birth,
            TIMESTAMPDIFF(YEAR, p.date_of_birth, CURDATE()) AS age,
            p.city,
            p.state_province
        FROM patient_demographics p
        WHERE p.patient_id = %s
    """, (patient_id,))
    patient = cursor.fetchone()

    if not patient:
        cursor.close()
        conn.close()
        return None

    cursor.execute("""
        SELECT COUNT(*) AS encounter_count
        FROM ehr_encounter
        WHERE patient_id = %s
    """, (patient_id,))
    patient["encounter_count"] = cursor.fetchone()["encounter_count"]

    cursor.execute("""
        SELECT COUNT(*) AS abnormal_lab_count
        FROM lab_result
        WHERE patient_id = %s
          AND abnormal_flag IS NOT NULL
          AND TRIM(abnormal_flag) <> ''
          AND UPPER(abnormal_flag) <> 'NORMAL'
    """, (patient_id,))
    patient["abnormal_lab_count"] = cursor.fetchone()["abnormal_lab_count"]

    cursor.execute("""
        SELECT COUNT(*) AS medication_count
        FROM pharmacy_medication
        WHERE patient_id = %s
    """, (patient_id,))
    patient["medication_count"] = cursor.fetchone()["medication_count"]

    cursor.execute("""
        SELECT COUNT(*) AS device_alert_count
        FROM remote_device_reading
        WHERE patient_id = %s
          AND data_quality_flag IS NOT NULL
          AND UPPER(data_quality_flag) <> 'GOOD'
    """, (patient_id,))
    patient["device_alert_count"] = cursor.fetchone()["device_alert_count"]

    cursor.execute("""
        SELECT
            encounter_id,
            chief_complaint,
            notes
        FROM ehr_encounter
        WHERE patient_id = %s
        ORDER BY encounter_id DESC
        LIMIT 5
    """, (patient_id,))
    patient["recent_encounters"] = cursor.fetchall()

    cursor.execute("""
        SELECT
            lab_result_id,
            test_name,
            result_value,
            result_numeric,
            abnormal_flag
        FROM lab_result
        WHERE patient_id = %s
        ORDER BY lab_result_id DESC
        LIMIT 5
    """, (patient_id,))
    patient["recent_labs"] = cursor.fetchall()

    cursor.execute("""
        SELECT
            medication_id,
            medication_name,
            dosage
        FROM pharmacy_medication
        WHERE patient_id = %s
        ORDER BY medication_id DESC
        LIMIT 5
    """, (patient_id,))
    patient["medications"] = cursor.fetchall()

    cursor.execute("""
        SELECT
            claim_id,
            claim_number,
            payer,
            claim_status
        FROM claims_encounter
        WHERE patient_id = %s
        ORDER BY claim_id DESC
        LIMIT 5
    """, (patient_id,))
    patient["claims"] = cursor.fetchall()

    cursor.execute("""
        SELECT
            procedure_id,
            procedure_code,
            procedure_description
        FROM procedure_record
        WHERE patient_id = %s
        ORDER BY procedure_id DESC
        LIMIT 5
    """, (patient_id,))
    patient["procedures"] = cursor.fetchall()

    cursor.execute("""
        SELECT
            device_id,
            device_type,
            measurement_type,
            measurement_value,
            measurement_unit,
            source_system,
            data_quality_flag
        FROM remote_device_reading
        WHERE patient_id = %s
        ORDER BY device_id DESC
        LIMIT 5
    """, (patient_id,))
    patient["device_readings"] = cursor.fetchall()

    cursor.close()
    conn.close()
    return patient


def run_unified_search(q: str, limit=50):
    like_q = f"%{q}%"

    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    query = """
    SELECT * FROM (
        SELECT
            e.patient_id,
            CONCAT(COALESCE(p.first_name, ''), ' ', COALESCE(p.last_name, '')) AS patient_name,
            e.notes AS note_text,
            'ehr_encounter' AS source_table,
            e.encounter_id AS source_record_id
        FROM ehr_encounter e
        JOIN patient_demographics p ON p.patient_id = e.patient_id
        WHERE e.notes LIKE %s
           OR e.chief_complaint LIKE %s

        UNION ALL

        SELECT
            l.patient_id,
            CONCAT(COALESCE(p.first_name, ''), ' ', COALESCE(p.last_name, '')) AS patient_name,
            CONCAT(l.test_name, ' = ', COALESCE(l.result_value, CAST(l.result_numeric AS CHAR))) AS note_text,
            'lab_result' AS source_table,
            l.lab_result_id AS source_record_id
        FROM lab_result l
        JOIN patient_demographics p ON p.patient_id = l.patient_id
        WHERE l.test_name LIKE %s
           OR l.abnormal_flag LIKE %s

        UNION ALL

        SELECT
            m.patient_id,
            CONCAT(COALESCE(p.first_name, ''), ' ', COALESCE(p.last_name, '')) AS patient_name,
            CONCAT(m.medication_name, ' ', COALESCE(m.dosage, '')) AS note_text,
            'pharmacy_medication' AS source_table,
            m.medication_id AS source_record_id
        FROM pharmacy_medication m
        JOIN patient_demographics p ON p.patient_id = m.patient_id
        WHERE m.medication_name LIKE %s

        UNION ALL

        SELECT
            c.patient_id,
            CONCAT(COALESCE(p.first_name, ''), ' ', COALESCE(p.last_name, '')) AS patient_name,
            CONCAT('Claim ', c.claim_number, ' status: ', COALESCE(c.claim_status, '')) AS note_text,
            'claims_encounter' AS source_table,
            c.claim_id AS source_record_id
        FROM claims_encounter c
        JOIN patient_demographics p ON p.patient_id = c.patient_id
        WHERE c.claim_number LIKE %s
           OR c.payer LIKE %s
           OR c.claim_status LIKE %s

        UNION ALL

        SELECT
            pr.patient_id,
            CONCAT(COALESCE(p.first_name, ''), ' ', COALESCE(p.last_name, '')) AS patient_name,
            CONCAT(pr.procedure_code, ' - ', COALESCE(pr.procedure_description, '')) AS note_text,
            'procedure_record' AS source_table,
            pr.procedure_id AS source_record_id
        FROM procedure_record pr
        JOIN patient_demographics p ON p.patient_id = pr.patient_id
        WHERE pr.procedure_code LIKE %s
           OR pr.procedure_description LIKE %s

        UNION ALL

        SELECT
            rd.patient_id,
            CONCAT(COALESCE(p.first_name, ''), ' ', COALESCE(p.last_name, '')) AS patient_name,
            CONCAT(
                COALESCE(rd.device_type, ''),
                ' ',
                COALESCE(rd.measurement_type, ''),
                ' = ',
                COALESCE(CAST(rd.measurement_value AS CHAR), ''),
                ' ',
                COALESCE(rd.measurement_unit, '')
            ) AS note_text,
            'remote_device_reading' AS source_table,
            rd.device_id AS source_record_id
        FROM remote_device_reading rd
        JOIN patient_demographics p ON p.patient_id = rd.patient_id
        WHERE rd.device_type LIKE %s
           OR rd.measurement_type LIKE %s
           OR rd.source_system LIKE %s
    ) x
    LIMIT %s
    """

    cursor.execute(query, (
        like_q, like_q,
        like_q, like_q,
        like_q,
        like_q, like_q, like_q,
        like_q, like_q,
        like_q, like_q, like_q,
        limit
    ))

    results = cursor.fetchall()
    cursor.close()
    conn.close()
    return results


def call_llm_search(query: str, timeout=12):
    """Call configured Ollama LLM to produce structured search results.
    Returns a list of result objects or None on failure.
    """
    ollama_host = os.getenv("OLLAMA_HOST")
    ollama_model = os.getenv("OLLAMA_MODEL")

    if not ollama_host or not ollama_model:
        return None

    # Include a short schema snippet to help the model (keeps prompt focused)
    schema_snippet = get_schema_snippet_for_query(query, max_chars=700)

    # Strict prompt: require ONLY JSON and provide a fail-safe minimal response format.
    prompt = (
        "You are a helpful clinical assistant. Given the user query and the database schema below, return EXACTLY valid JSON and nothing else." +
        "\n\nReturn a top-level object with a single key \"results\" which is an array. Each item must be an object with: \"title\" (short string), \"description\" (one-line string), optionally \"meta\" (string), optionally \"score\" (float between 0.0 and 1.0), optionally \"patient_id\" (string or number)." +
        "\n\nIf you cannot find relevant items, return {\"results\":[]}." +
        "\n\nSchema (short):\n" + schema_snippet +
        "\n\nUser query: \"" + query + "\"\n\n" +
        "Examples of valid responses:\n" +
        "{\"results\": [{\"title\":\"Chest pain note\",\"description\":\"Patient John Smith: chest pain and SOB\",\"meta\":\"ehr_encounter:123\",\"score\":0.92,\"patient_id\":\"P001\"}]}\n" +
        "{\"results\": []}\n\nReturn only the JSON object (no markdown, no explanation, no surrounding text, no backticks)."
    )

    # Try a couple of deterministic requests (low temperature), log raw text for debugging on failures.
    attempts = [ {"temperature": 0.0, "top_p": 0.1}, {"temperature": 0.1, "top_p": 0.9} ]
    raw_text = None
    for opts in attempts:
        try:
            resp = requests.post(
                f"{ollama_host}/api/generate",
                json={
                    "model": ollama_model,
                    "prompt": prompt,
                    "stream": False,
                    "options": {"temperature": opts["temperature"], "top_p": opts["top_p"]}
                },
                timeout=timeout
            )
            if resp.status_code != 200:
                continue

            body = resp.json()
            raw_text = body.get("response") if isinstance(body, dict) else None
            if not raw_text:
                continue

            # Attempt to parse JSON directly
            try:
                parsed = json.loads(raw_text)
                raw_results = parsed.get("results") if isinstance(parsed, dict) else None
            except Exception:
                # attempt to extract JSON substring
                raw_results = None
                m = re.search(r"(\{\s*\"results\"[\s\S]*\})", raw_text)
                if m:
                    try:
                        parsed = json.loads(m.group(1))
                        raw_results = parsed.get("results")
                    except Exception:
                        raw_results = None

            # Validate and sanitize results
            validated = validate_llm_results(raw_results)
            if validated:
                return validated
            # else continue to next attempt

        except Exception:
            raw_text = None
            continue

    # If we reach here, all LLM attempts failed to produce validated results.
    try:
        log_path = BASE_DIR / "llm_debug.log"
    except Exception:
        log_path = Path("llm_debug.log")

    try:
        with open(log_path, 'a', encoding='utf-8') as lf:
            from datetime import datetime
            lf.write(f"--- {datetime.utcnow().isoformat()}Z QUERY: {query}\n")
            lf.write((raw_text or "<no-response>") + "\n\n")
    except Exception:
        pass

    # As a last resort, synthesize LLM-like results from the DB so the LLM-path returns useful data
    try:
        search_q = simplify_query_for_db(query)
        raw = run_unified_search(search_q, limit=20)
        emu = []
        for r in raw[:20]:
            title = r.get("patient_name") or f"Patient {r.get('patient_id') or ''}".strip()
            desc = r.get("note_text") or ''
            meta = r.get("source_table")
            emu.append({"title": title, "description": desc, "meta": f"synthetic:{meta}", "score": 0.65, "patient_id": r.get("patient_id")})
        return emu if emu else None
    except Exception:
        return None


@app.route("/api/llm_search", methods=["POST"])
def llm_search():
    try:
        data = request.get_json(silent=True) or {}
        q = (data.get("query") or "").strip()
        if not q:
            return jsonify({"results": []})

        # Try LLM first
        llm_results = call_llm_search(q)
        if llm_results:
            return jsonify({"results": llm_results})

        # Fallback to DB unified search (use a simplified query for better LIKE matches)
        search_q = simplify_query_for_db(q)
        raw = run_unified_search(search_q, limit=20)
        mapped = []
        for r in raw:
            title = r.get("patient_name") or f"Patient {r.get('patient_id') or ''}".strip()
            desc = r.get("note_text") or ''
            meta = r.get("source_table")
            mapped.append({"title": title, "description": desc, "meta": meta, "score": 0.5, "patient_id": r.get("patient_id")})

        return jsonify({"results": mapped})

    except Error as e:
        return jsonify({"error": str(e)}), 500
    except Exception as e:
        return jsonify({"error": str(e)}), 500


def build_chat_response(message: str):
    intent = classify_intent(message)
    limit = extract_limit(message, default=10, max_limit=50)

    if intent == "help":
        return {
            "reply": (
                "I can help with dashboard stats, patient lists, patient summaries, "
                "and keyword searches across encounters, labs, medications, claims, procedures, and device readings."
            ),
            "intent": intent,
            "data": {
                "examples": [
                    "Show dashboard stats",
                    "List 10 patients",
                    "Find abnormal glucose labs",
                    "Search metformin",
                    "Show patient John Smith"
                ]
            }
        }

    if intent == "stats":
        stats = fetch_stats_data()
        return {
            "reply": (
                f"There are {stats['total_patients']} patients, {stats['total_encounters']} encounters, "
                f"{stats['abnormal_labs']} abnormal labs, and {stats['high_risk_patients']} high-risk patients."
            ),
            "intent": intent,
            "data": stats
        }

    if intent == "patients":
        patients = fetch_patient_list(limit)
        if patients:
            session["last_patient_id"] = patients[0]["patient_id"]
        return {
            "reply": f"I found {len(patients)} patients.",
            "intent": intent,
            "data": {"patients": patients}
        }

    patient_name = extract_patient_name(message)
    if patient_name:
        patient = find_patient_by_name(patient_name)
        if patient:
            session["last_patient_id"] = patient["patient_id"]
            details = get_patient_summary(patient["patient_id"])
            return {
                "reply": f"I found {details['patient_name']} and loaded their summary.",
                "intent": "patient_summary",
                "data": {"patient": details}
            }
        return {
            "reply": f"I could not find a patient matching '{patient_name}'.",
            "intent": "patient_summary",
            "data": {"patient": None}
        }

    if intent == "followup":
        last_patient_id = session.get("last_patient_id")
        if last_patient_id:
            details = get_patient_summary(last_patient_id)
            if details:
                return {
                    "reply": f"Here are more details for {details['patient_name']}.",
                    "intent": "patient_summary",
                    "data": {"patient": details}
                }
        return {
            "reply": "I do not have a recent patient in context yet. Ask for a patient by name or list patients first.",
            "intent": intent,
            "data": {}
        }

    if intent in ["search", "general_search"]:
        results = run_unified_search(message, limit=limit)
        if results:
            first_patient_id = results[0].get("patient_id")
            if first_patient_id:
                session["last_patient_id"] = first_patient_id
        return {
            "reply": f"I found {len(results)} matching records for '{message}'.",
            "intent": "search",
            "data": {"results": results}
        }

    return {
        "reply": "I could not understand that request.",
        "intent": "unknown",
        "data": {}
    }


@app.route("/api/health", methods=["GET"])
def health():
    try:
        conn = get_connection()
        conn.close()
        return jsonify({"status": "ok"})
    except Error as e:
        return jsonify({"status": "error", "error": str(e)}), 500


@app.route("/api/patients", methods=["GET"])
def get_patients():
    try:
        limit = safe_int(request.args.get("limit", 10), 10)
        limit = min(max(limit, 1), 50)
        rows = fetch_patient_list(limit)
        return jsonify({"patients": rows})
    except Error as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/stats", methods=["GET"])
def get_stats():
    try:
        stats = fetch_stats_data()
        return jsonify(stats)
    except Error as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/search", methods=["POST"])
def search():
    try:
        data = request.get_json(silent=True) or {}
        q = (data.get("query") or "").strip()

        if not q:
            return jsonify({"results": []})

        results = run_unified_search(q, limit=50)
        if results:
            first_patient_id = results[0].get("patient_id")
            if first_patient_id:
                session["last_patient_id"] = first_patient_id

        return jsonify({"results": results})
    except Error as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/chat", methods=["POST"])
def chat():
    try:
        data = request.get_json(silent=True) or {}
        message = (data.get("message") or "").strip()

        if not message:
            return jsonify({
                "reply": "Please enter a message.",
                "intent": "empty",
                "data": {}
            })

        response = build_chat_response(message)
        return jsonify(response)

    except Error as e:
        return jsonify({
            "reply": "Database error.",
            "intent": "error",
            "error": str(e)
        }), 500
    except Exception as e:
        return jsonify({
            "reply": "Unexpected server error.",
            "intent": "error",
            "error": str(e)
        }), 500


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=True)