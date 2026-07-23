import os
import sys
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

api_key = os.getenv("GOOGLE_API_KEY")
if not api_key:
    print("❌ ERROR: GOOGLE_API_KEY tidak ditemukan!")
    print("Silakan buat file '.env' di folder ini dan isi dengan: GOOGLE_API_KEY=AIzaSy...")
    sys.exit(1)

from llama_index.core import SimpleDirectoryReader, VectorStoreIndex, StorageContext
from llama_index.core import Settings
from llama_index.embeddings.google_genai import GoogleGenAIEmbedding
from llama_index.llms.google_genai import GoogleGenAI
import chromadb
from llama_index.vector_stores.chroma import ChromaVectorStore

print("🚀 Memulai VulnCopilot Minimal RAG Engine...")

# 1. Konfigurasi Embedding & LLM Gemini
print("📦 Menyiapkan Model Gemini (LLM & Embeddings)...")
embed_model = GoogleGenAIEmbedding(
    model_name="gemini-embedding-2-preview", api_key=api_key
)
llm = GoogleGenAI(model="gemini-flash-latest", api_key=api_key)

Settings.embed_model = embed_model
Settings.llm = llm

# 2. Membaca Dokumen Keamanan dari folder ./data
print("📄 Membaca dokumen dari folder ./data ...")
data_path = os.path.join(os.path.dirname(__file__), "data")
documents = SimpleDirectoryReader(data_path).load_data()
print(f"✅ Berhasil memuat {len(documents)} bagian/dokumen.")

# 3. Setup Vector Store lokal (ChromaDB)
print("💾 Menyiapkan Database Vektor Lokal (ChromaDB)...")
db_path = os.path.join(os.path.dirname(__file__), "chroma_db")
db = chromadb.PersistentClient(path=db_path)
chroma_collection = db.get_or_create_collection("vuln_copilot_kb")
vector_store = ChromaVectorStore(chroma_collection=chroma_collection)
storage_context = StorageContext.from_defaults(vector_store=vector_store)

# 4. Melakukan Indexing Dokumen ke ChromaDB
print("🧠 Membuat Vector Embeddings & Menyimpan ke Database...")
index = VectorStoreIndex.from_documents(
    documents, storage_context=storage_context
)
print("✅ Indexing selesai!")

# 5. Menjalankan Query Engine
query_engine = index.as_query_engine(similarity_top_k=3)

# Interactive Loop
print("\n" + "="*50)
print("🛡️ VulnCopilot CLI Siap! Ketik 'exit' untuk keluar.")
print("="*50 + "\n")

while True:
    try:
        user_query = input("❓ Tanya VulnCopilot > ")
        if user_query.strip().lower() in ["exit", "quit", "keluar"]:
            print("Sampai jumpa!")
            break
        if not user_query.strip():
            continue
        
        print("\n🔍 Mencari referensi keamanan & menganalisis...")
        response = query_engine.query(user_query)
        print("\n🤖 Respon VulnCopilot:\n")
        print(response)
        print("\n" + "-"*50 + "\n")
    except KeyboardInterrupt:
        print("\nSampai jumpa!")
        break
    except Exception as e:
        print(f"\n❌ Terjadi kesalahan: {e}\n")
