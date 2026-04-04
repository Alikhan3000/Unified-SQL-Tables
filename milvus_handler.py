from pymilvus import connections, FieldSchema, CollectionSchema, DataType, Collection, utility
from sentence_transformers import SentenceTransformer
from dotenv import load_dotenv
import os
import numpy as np

load_dotenv()

class MilvusHandler:
    def __init__(self):
        self.host = os.getenv("MILVUS_HOST", "localhost")
        self.port = os.getenv("MILVUS_PORT", "19530")
        self.collection_name = "clinical_notes"
        self.embedding_model = SentenceTransformer(os.getenv("EMBEDDING_MODEL", "all-MiniLM-L6-v2"))
        self.dim = 384  # all-MiniLM-L6-v2 dimension
        print("🔄 Connecting to Milvus...")
        self.connect()
        self.create_collection()
        print("✅ Milvus ready!")

    def connect(self):
        """Connect to Milvus server"""
        try:
            connections.connect(alias="default", host=self.host, port=self.port)
            print(f"✅ Connected to Milvus at {self.host}:{self.port}")
        except Exception as e:
            print(f"❌ Milvus connection failed: {e}")
            print("💡 Make sure Milvus is running on localhost:19530")

    def create_collection(self):
        """Create clinical notes collection if it doesn't exist"""
        if utility.has_collection(self.collection_name):
            self.collection = Collection(self.collection_name)
            self.collection.load()
            print(f"✅ Using existing collection: {self.collection_name}")
            return

        fields = [
            FieldSchema(name="id", dtype=DataType.INT64, is_primary=True, auto_id=True),
            FieldSchema(name="patient_id", dtype=DataType.INT64),
            FieldSchema(name="source_table", dtype=DataType.VARCHAR, max_length=50),
            FieldSchema(name="source_record_id", dtype=DataType.INT64),
            FieldSchema(name="note_text", dtype=DataType.VARCHAR, max_length=5000),
            FieldSchema(name="embedding", dtype=DataType.FLOAT_VECTOR, dim=self.dim),
        ]

        schema = CollectionSchema(fields, description="Clinical notes embeddings")
        self.collection = Collection(name=self.collection_name, schema=schema)

        # Create IVF_FLAT index for fast similarity search
        index_params = {
            "index_type": "IVF_FLAT",
            "metric_type": "L2",
            "params": {"nlist": 128}
        }
        self.collection.create_index(field_name="embedding", index_params=index_params)
        self.collection.load()
        print(f"✅ Created Milvus collection: {self.collection_name}")

    def insert_notes(self, rows):
        """Insert notes with embeddings into Milvus"""
        if not rows:
            print("⚠️ No notes to insert")
            return

        print(f"🔄 Embedding {len(rows)} notes...")
        texts = [row["note_text"] for row in rows]
        embeddings = self.embedding_model.encode(texts).tolist()

        data = [
            [int(row["patient_id"]) for row in rows],
            [row["source_table"] for row in rows],
            [int(row["source_record_id"]) for row in rows],
            texts,
            embeddings
        ]

        self.collection.insert(data)
        self.collection.flush()
        print(f"✅ Inserted {len(rows)} clinical note embeddings into Milvus!")

    def search_notes(self, query, limit=5):
        """Find semantically similar clinical notes"""
        try:
            query_embedding = self.embedding_model.encode([query]).tolist()
            self.collection.load()

            search_params = {"metric_type": "L2", "params": {"nprobe": 10}}
            results = self.collection.search(
                data=query_embedding,
                anns_field="embedding",
                param=search_params,
                limit=limit,
                output_fields=["patient_id", "source_table", "source_record_id", "note_text"]
            )

            matches = []
            for hits in results:
                for hit in hits:
                    matches.append({
                        "patient_id": hit.entity.get("patient_id"),
                        "source_table": hit.entity.get("source_table"),
                        "source_record_id": hit.entity.get("source_record_id"),
                        "note_text": hit.entity.get("note_text"),
                        "distance": float(hit.distance)
                    })
            return matches[:limit]
        except Exception as e:
            print(f"❌ Milvus search error: {e}")
            return []