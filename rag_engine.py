import os
import sys
from dotenv import load_dotenv

#load env
load_dotenv()

api_key = os.getenv("GOOGLE_API_KEY")
if not api_key:
    raise ValueError("GOOGLE_API_KEY not found in .env file")

from llma_index.core import(
    SimpleDirectoryReader,
    VectorStoreIndex,
    StorageContext,
    Settings,
)

from llama_index.core.node_parser import MarkdownNodeParser
from llama_index.core.memory import ChatMemoryBuffer
from llama_index.embeddings.google_genai import GoogleGenAIEmbedding
from llama_index.llms.google_genai import GoogleGenAI
import chromadb
from llama_index.vector_stores.chroma import ChromaVectorStore

class VulnCopilotRAG:
    def __init__(self):
        print("📦 Menyiapkan Model Gemini (Embeddings & LLM)...")
        self.embed_model = GoogleGenAIEmbedding(
            model_name="gemini-embedding-2-preview", api_key=api_key
        )
        self.llm = GoogleGenAI(
            model="gemini-flash-latest", api_key=api_key, temperature=0.2
        )
        Settings.llm = self.llm
        Settings.embed_model = self.embed_model
        self.chat_engine = None
        self._init_engine()
    
    def _init_engine(self):
        print("💾 Membuka Database Vektor (ChromaDB)...")
        db_path = os.path.join(os.path.dirname(__file__), "chroma_db")
        db = chromadb.PersistentClient(path=db_path)
        chroma_collection = db.get_or_create_collection("vuln_copilot_kb_v3")
        vector_store = ChromaVectorStore(chroma_collection=chroma_collection)
        storage_context = StorageContext.from_defaults(vector_store=vector_store)

        if chroma_collection.count() > 0:
            print(f"✅ Memuat index yang sudah ada dari ChromaDB ({chroma_collection.count()} data terdeteksi)...")
            index = VectorStoreIndex.from_vector_store(
                vector_store, storage_context=storage_context
            )
        else:
            print("📄 Membaca dokumen dari ./data dan melakukan chunking...")
            data_path = os.path.join(os.path.dirname(__file__), "data")
            documents = SimpleDirectoryReader(data_path).load_data()
            parser = MarkdownNodeParser()
            nodes = parser.get_nodes_from_documents(documents)

            #enrich metadata
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
            
            print(f"🧠 Melakukan Indexing {len(nodes)} nodes ke ChromaDB...")
            index = VectorStoreIndex(nodes, storage_context=storage_context)
            print("✅ Indexing selesai!")

        memory = ChatMemoryBuffer.from_defaults(token_limit=3000)
        chat_context_prompt = (
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
            "Jika informasi tidak terdapat pada dokumen referensi, sampaikan dengan jujur bahwa informasi tidak tersedia di Knowledge Base."
        )

        self.chat_engine = index.as_chat_engine(
            chat_mode="condense_plus_context",
            memory=memory,
            similarity_top_k=3,
            context_prompt=chat_context_prompt,
            verbose=False
        )


    def query(self, message: str) -> str:
        if not self.chat_engine:
            raise RuntimeError("RAG Engine belum diinisialisasi!")
        response = self.chat_engine.chat(message)
        return str(response)
        
    def reset_memory(self):
        if self.chat_engine and hasattr(self.chat_engine, "memory"):
            self.chat_engine.memory.reset()
            return True
        return False
