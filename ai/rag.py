import os
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_community.vectorstores import FAISS
import google.generativeai as genai
from dotenv import load_dotenv
from config import CHUNK_SIZE, CHUNK_OVERLAP, EMBEDDING_MODEL, CHAT_MODEL, DOCUMENTS_DIR, VECTORSTORE_DIR, RETRIEVAL_K

load_dotenv()
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))


def build_vectorstore():
    """Loads all PDFs from documents/, splits, embeds, saves to disk."""
    # your job:
    # 1. loop through every .pdf file in DOCUMENTS_DIR
    all_pages = []
    # 2. load each with PyPDFLoader, collect all pages into one list
    for filename in os.listdir(DOCUMENTS_DIR):
        if filename.endswith(".pdf"):
            file_path = os.path.join(DOCUMENTS_DIR, filename)
            loader = PyPDFLoader(file_path)
            pages = loader.load()
            all_pages.extend(pages) # add these pages to the big list
    print(f"Total pages loaded: {len(all_pages)}")

    # 3. split all pages into chunks using RecursiveCharacterTextSplitter

    splitter = RecursiveCharacterTextSplitter(chunk_size = CHUNK_SIZE, chunk_overlap = CHUNK_OVERLAP)
    chunks = splitter.split_documents(all_pages)
    # 4. build embeddings + FAISS vectorstore (like your notebook)
    embeddings = GoogleGenerativeAIEmbeddings(model=EMBEDDING_MODEL)
    vectorstore = FAISS.from_documents(chunks, embeddings)
    # 5. NEW: save it — vectorstore.save_local(VECTORSTORE_DIR)

    vectorstore.save_local(VECTORSTORE_DIR)


def load_vectorstore():
    """Loads the already-built vectorstore from disk — fast, no re-embedding."""
    # your job:
    # 1. create the same embeddings object
    # 2. FAISS.load_local(VECTORSTORE_DIR, embeddings, allow_dangerous_deserialization=True)
    # 3. return it
    """Loads the already-built vectorstore from disk — fast, no re-embedding."""
    embeddings = GoogleGenerativeAIEmbeddings(model=EMBEDDING_MODEL)
    vectorstore = FAISS.load_local(
        VECTORSTORE_DIR,
        embeddings,
        allow_dangerous_deserialization=True
    )
    return vectorstore


def ask_document(vectorstore, question,  k=RETRIEVAL_K):
    """Same logic as your notebook's ask_document(), but vectorstore is passed in."""
    results = vectorstore.similarity_search(question, k=k)
    context = "\n\n".join([doc.page_content for doc in results])
    # Step 2 — build the prompt
    prompt = f"""
You are an expert on the CPA7-LD-4040 RO membrane datasheet.
Answer the operator's question using ONLY the context below.
If the answer is not in the context, say so clearly.

CONTEXT:
{context}

QUESTION:
{question}
"""
    # Step 3 — send to Gemini
    model = genai.GenerativeModel(CHAT_MODEL)
    response = model.generate_content(prompt)
    return response.text


if __name__ == "__main__":
    vs = load_vectorstore()
    answer = ask_document(vs, "What is the maximum pressure drop allowed?")
    print(answer)