import os
import sys
from dotenv import load_dotenv

#env load
load_dotenv()
api_key = os.getenv("GOOGLE_API_KEY")
if not api_key:
    print("❌ ERROR: GOOGLE_API_KEY tidak ditemukan di file .env!")
    sys.exit(1)

# Import modul LlamaIndex & ChromaDB
from llama_index.core import SimpleDirectoryReader, VectorStoreIndex, StorageContext, Settings, PromptTemplate
from llama_index.core.node_parser import MarkdownNodeParser
from llama_index.embeddings.google_genai import GoogleGenAIEmbedding
from llama_index.llms.google_genai import GoogleGenAI
import chromadb
from llama_index.vector_stores.chroma import ChromaVectorStore
from llama_index.core.vector_stores import MetadataFilters, ExactMatchFilter

print("Starting VulnCopilot (markdown chunking)")

#konfig model
print("📦 Menyiapkan Model Gemini...")
embed_model = GoogleGenAIEmbedding(
    model_name="gemini-embedding-2-preview", api_key=api_key
)
llm = GoogleGenAI(model="gemini-flash-latest", api_key=api_key)
Settings.embed_model = embed_model
Settings.llm = llm

#dokumen reading
print("📄 Membaca dokumen dari folder ./data ...")
data_path = os.path.join(os.path.dirname(__file__), "data")
documents = SimpleDirectoryReader(data_path).load_data()

#Chungking: MarkDownNodeParser
print("Running MarkDownNodeParser by header markdown")
parser = MarkdownNodeParser()
nodes = parser.get_nodes_from_documents(documents)
print(f"✅ Dokumen berhasil dipotong menjadi {len(nodes)} nodes/chunks terstruktur!")

# 5. Metadata Enrichment (Step 2 Feature)
print("🏷️ Menambahkan Tag Metadata (Category, CWE ID, Severity)...")
for node in nodes:
    header_path = str(node.metadata.get("header_path", "")).lower()
    content = node.get_content().lower()
    
    if "a01" in header_path or "access control" in content:
        node.metadata["category"] = "Access Control"
        node.metadata["cwe_id"] = "CWE-200"
        node.metadata["severity"] = "High"
    elif "a02" in header_path or "crypto" in content:
        node.metadata["category"] = "Cryptography"
        node.metadata["cwe_id"] = "CWE-311"
        node.metadata["severity"] = "Critical"
    elif "a03" in header_path or "injection" in content:
        node.metadata["category"] = "Injection"
        node.metadata["cwe_id"] = "CWE-89"
        node.metadata["severity"] = "Critical"
    else:
        node.metadata["category"] = "General Security"
        node.metadata["cwe_id"] = "CWE-General"
        node.metadata["severity"] = "Medium"
print(f"✅ Dokumen berhasil dipotong menjadi {len(nodes)} nodes dengan Metadata!")

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
chroma_collection = db.get_or_create_collection("vuln_copilot_kb_v3")
vector_store = ChromaVectorStore(chroma_collection=chroma_collection)
storage_context = StorageContext.from_defaults(vector_store=vector_store)

#Indexing nodes
index = VectorStoreIndex(nodes, storage_context=storage_context)
print("Indexing to ChromaDB finished!")

#open Query Engine with prompt
print("🎯 Menyiapkan DevSecOps System Prompt Template...")
qa_prompt_tmpl = PromptTemplate(
    "Anda adalah seorang Senior DevSecOps & Application Security Specialist (VulnCopilot).\n"
    "Gunakan konteks dokumen referensi keamanan berikut untuk menganalisis dan menjawab pertanyaan:\n"
    "---------------------\n"
    "{context_str}\n"
    "---------------------\n"
    "Jawablah pertanyaan pengguna dengan format laporan audit keamanan terstruktur berikut:\n\n"
    "🔍 1. Ringkasan Ancaman:\n"
    "<Berikan penjelasan singkat tentang kerentanan/masalah>\n\n"
    "💥 2. Dampak Risiko (Security Impact):\n"
    "<Berikan potensi dampak bahaya bagi aplikasi/sistem>\n\n"
    "🛠️ 3. Rekomendasi Perbaikan & Kode (Remediation):\n"
    "<Berikan rekomendasi perbaikan dan contoh kode jika ada di dokumen>\n\n"
    "📚 4. Referensi:\n"
    "<Sebutkan sumber referensi dari dokumen yang dirujuk>\n\n"
    "Jika informasi tidak terdapat pada dokumen referensi, sampaikan dengan jujur bahwa informasi tidak tersedia di Knowledge Base.\n\n"
    "Pertanyaan: {query_str}\n"
    "Jawaban VulnCopilot:"
)
# Mengaktifkan Query Engine dengan DevSecOps System Prompt
query_engine = index.as_query_engine(
    similarity_top_k=3,
    text_qa_template=qa_prompt_tmpl
)

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
