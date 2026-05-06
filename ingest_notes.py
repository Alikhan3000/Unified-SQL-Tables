from database_handler import DatabaseHandler
from sentence_transformers import SentenceTransformer
from pymilvus import connections, utility, FieldSchema, CollectionSchema, DataType, Collection

COLLECTION_NAME = "clinical_notes"
DIMENSION = 384
BATCH_SIZE = 64

def chunk_text(text, max_chars=800):
    text = (text or "").strip()
    if not text:
        return []
    if len(text) <= max_chars:
        return [text]

    chunks = []
    start = 0
    while start < len(text):
        end = min(start + max_chars, len(text))
        chunk = text[start:end].strip()
        if len(chunk) >= 30:
            chunks.append(chunk)
        start = end
    return chunks

def recreate_collection():
    if utility.has_collection(COLLECTION_NAME):
        utility.drop_collection(COLLECTION_NAME)

    fields = [
        FieldSchema(name="id", dtype=DataType.INT64, is_primary=True, auto_id=False),
        FieldSchema(name="patient_id", dtype=DataType.INT64),
        FieldSchema(name="source_record_id", dtype=DataType.INT64),
        FieldSchema(name="encounter_type", dtype=DataType.VARCHAR, max_length=100),
        FieldSchema(name="encounter_start", dtype=DataType.VARCHAR, max_length=50),
        FieldSchema(name="chief_complaint", dtype=DataType.VARCHAR, max_length=255),
        FieldSchema(name="note_text", dtype=DataType.VARCHAR, max_length=2000),
        FieldSchema(name="embedding", dtype=DataType.FLOAT_VECTOR, dim=DIMENSION),
    ]

    schema = CollectionSchema(fields=fields, description="EHR encounter clinical notes")
    collection = Collection(name=COLLECTION_NAME, schema=schema)

    index_params = {
        "index_type": "IVF_FLAT",
        "metric_type": "L2",
        "params": {"nlist": 128}
    }
    collection.create_index(field_name="embedding", index_params=index_params)
    return collection

def main():
    print("Connecting to MySQL...")
    db = DatabaseHandler()

    print("Connecting to Milvus...")
    connections.connect(alias="default", host="127.0.0.1", port="19530")

    print("Loading embedding model...")
    model = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")

    print("Creating collection...")
    collection = recreate_collection()

    query = """
    SELECT 
        encounter_id AS source_record_id,
        patient_id,
        encounter_type,
        encounter_start,
        chief_complaint,
        notes AS note_text
    FROM ehr_encounter
    WHERE notes IS NOT NULL AND TRIM(notes) <> ''
    """

    result = db.execute_query(query)

    if not result or 'data' not in result or not result['data']:
        print("No notes found.")
        return

    rows = result['data']
    print(f"Found {len(rows)} encounter notes")

    prepared = []
    current_id = 1

    for row in rows:
        note_chunks = chunk_text(row.get("note_text", ""))

        for chunk in note_chunks:
            prepared.append({
                "id": current_id,
                "patient_id": int(row["patient_id"]),
                "source_record_id": int(row["source_record_id"]),
                "encounter_type": str(row.get("encounter_type") or "")[:100],
                "encounter_start": str(row.get("encounter_start") or "")[:50],
                "chief_complaint": str(row.get("chief_complaint") or "")[:255],
                "note_text": str(chunk)[:2000]
            })
            current_id += 1

    print(f"Prepared {len(prepared)} note chunks")

    for i in range(0, len(prepared), BATCH_SIZE):
        batch = prepared[i:i+BATCH_SIZE]
        texts = [x["note_text"] for x in batch]
        embeddings = model.encode(texts).tolist()

        data = [
            [x["id"] for x in batch],
            [x["patient_id"] for x in batch],
            [x["source_record_id"] for x in batch],
            [x["encounter_type"] for x in batch],
            [x["encounter_start"] for x in batch],
            [x["chief_complaint"] for x in batch],
            [x["note_text"] for x in batch],
            embeddings
        ]

        collection.insert(data)
        print(f"Inserted batch {i // BATCH_SIZE + 1}")

    collection.flush()
    collection.load()

    print("Done. Clinical notes are now in Milvus.")

if __name__ == "__main__":
    main()