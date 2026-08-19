# config.py

# Gemini models
CHAT_MODEL = "gemini-2.5-flash"
EMBEDDING_MODEL = "models/gemini-embedding-001"

# RAG settings
CHUNK_SIZE = 500
CHUNK_OVERLAP = 50
RETRIEVAL_K = 4

# File paths
DOCUMENTS_DIR = "documents"
VECTORSTORE_DIR = "vectorstore"

# RO thresholds (from earlier config.py plan)
DP_WATCH = 6.5
DP_ACTION = 6.8
MAX_CONDUCTIVITY = 125