from database_handler import DatabaseHandler
from milvus_handler import MilvusHandler

print("🚀 Loading clinical notes into Milvus...")
db = DatabaseHandler()
milvus = MilvusHandler()

notes = db.get_notes_for_embedding()
milvus.insert_notes(notes)
print("🎉 Milvus is ready for semantic search!")