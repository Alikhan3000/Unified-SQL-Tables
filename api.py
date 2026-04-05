from flask import Flask, request, jsonify
from flask_cors import CORS
from healthcare_chatbot import HealthcareChatbot

app = Flask(__name__)
CORS(app, resources={r"/api/*": {"origins": ["http://localhost:3000", "http://127.0.0.1:3000"]}})

bot = HealthcareChatbot()

@app.route('/api/stats', methods=['GET'])
def stats():
    stats_query = """
    SELECT 
        (SELECT COUNT(*) FROM patient_demographics) AS patients,
        (SELECT COUNT(*) FROM ehr_encounter) AS encounters,
        (SELECT COUNT(*) FROM lab_result WHERE abnormal_flag <> 'Normal') AS labs,
        (SELECT COUNT(*) FROM pharmacy_medication) AS meds,
        (SELECT COUNT(*) FROM procedure_record WHERE notes IS NOT NULL AND TRIM(notes) <> '') +
        (SELECT COUNT(*) FROM ehr_encounter WHERE notes IS NOT NULL AND TRIM(notes) <> '') AS notes
    """
    result = bot.db.execute_query(stats_query)

    if not result or 'data' not in result or not result['data']:
        return jsonify({'error': 'Unable to load stats from database'}), 500

    row = result['data'][0]
    return jsonify({
        'patients': row.get('patients', 0),
        'encounters': row.get('encounters', 0),
        'labs': row.get('labs', 0),
        'meds': row.get('meds', 0),
        'notes': row.get('notes', 0)
    })

@app.route('/api/search', methods=['POST'])
def search():
    data = request.get_json(silent=True) or {}
    query = (data.get('query') or '').strip()

    if not query:
        return jsonify({'error': 'Query is required'}), 400

    response = bot.get_response(query)

    return jsonify({
        'results': [{
            'title': 'HealthDataBot Response',
            'content': response,
            'type': 'milvus' if 'milvus' in response.lower() else 'response'
        }]
    })

if __name__ == '__main__':
    print("API ready on http://localhost:5000")
    app.run(host='0.0.0.0', port=5000, debug=True)