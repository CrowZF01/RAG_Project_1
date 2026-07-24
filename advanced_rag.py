import os
import sys
from dotenv import load_dotenv

#env load
load_dotenv()

api_key = os.getenv("GOOGLE_API_KEY")
if not api_key:
    print("ERROR: API Key not found in file .env!")
    sys.exit(1)

from llama_index.core import SimpleDirectoryReader, VectorStoreIndex, StorageContext
from llama_index.core import Settings
from llama_index.embeddings.google_genai import GoogleGenAIEmbedding
from llama_index.llms.google_genai import GoogleGenAI
import chromadb
from llama_index.vector_stores.chroma import ChromaVectorStore

print("Starting VulnCopilot (markdown chunking)")

#konfig model
print("Menyiapkan Model")
embed_model = GoogleGenAIEmbedding(
    model_name="gemini-embedding-2-preview", api_key=api_key
)
llm = GoogleGenAI(model="gemini-flash-latest", api_key=api_key)

Settings.embed_model = embed_model
Settings.llm = llm

#dokumen reading
print("Memuat dokumen dari folder ./data")
data_path = os.path.join(os.path.dirname(__file__), "data")
documents = SimpleDirectoryReader(data_path).load_data()

#Chungking: MarkDownNodeParser
print("Running MarkDownNodeParser by header markdown")
parser = MarkDownNodeParser()
nodes = parser.get_nodes_from_documents(documents)
print(f"✅ Dokumen berhasil dipotong menjadi {len(nodes)} nodes/chunks terstruktur!")

#PREVIEW 2 NODE PERTAMA
print("\n" + "="*50)
print("🔍 Preview Hasil Node/Chunking:")
for i, node in enumerate(nodes[:2]):
    print(f"\n--- Node {i+1} ---")
    print(f"📌 Metadata Header: {node.metadata}")
    print(f"📝 Isi Konten (Snippet):\n{node.get_content()[:200]}...")
print("="*50 + "\n")


#setup vector database
print("💾 Menyimpan Nodes ke Database Vektor (ChromaDB)...")
db_path = os.path.join(os.path.dirname(__file__), "chroma_db")
db = chromadb.PersistentClient(path=db_path)
chroma_collection = db.get_or_create_collection("vuln_copilot_kb_v2")
vector_store = ChromaVectorStore(chroma_collection=chroma_collection)
storage_context = StorageContext.from_defaults(vector_store=vector_store)

#Indexing nodes
index = VectorStoreIndex(nodes, storage_context=storage_context)
print("Indexing to ChromaDB finished!")
#query open
query_engine = index.as_query_engine(similiarity_top_k=3)

# 8. Interactive CLI Loop
print("\n" + "="*50)
print("🛡️ VulnCopilot Advanced RAG CLI Siap! Ketik 'exit' untuk keluar.")
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
