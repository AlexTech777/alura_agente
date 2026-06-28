"""
Alura Agente - agente de IA que responde preguntas sobre la documentacion interna
de la empresa, en MULTIPLES FORMATOS: PDF, Word, Excel, PowerPoint, Markdown, CSV,
JSON y HTML.

Arquitectura:
1. Se recorre la carpeta data/ y, segun la extension de cada archivo, se usa un
   lector especifico para extraer su texto (ver loaders.py).
2. El texto de cada documento se divide en fragmentos (chunks).
3. Cada fragmento se convierte en un vector con GoogleGenerativeAIEmbeddings.
4. Los vectores se guardan en un indice FAISS (busqueda por similitud).
5. Ante una pregunta, se buscan los fragmentos mas relevantes (sin importar el
   formato de origen) y se los pasa, junto con la pregunta, al modelo Gemini para
   generar la respuesta final (patron RAG: Retrieval-Augmented Generation).
"""
import os
import sys
from dotenv import load_dotenv

load_dotenv()  # carga automáticamente las variables definidas en el archivo .env

from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS
from langchain_google_genai import GoogleGenerativeAIEmbeddings, ChatGoogleGenerativeAI
from langchain.chains import RetrievalQA

from loaders import load_all_documents

# Carpeta con TODOS los documentos que el agente debe leer (cualquier formato soportado).
DATA_DIR = os.environ.get("AGENT_DATA_DIR", "data")
INDEX_PATH = "data/faiss_index"


def build_or_load_index():
    """Crea el indice FAISS si no existe, o lo carga si ya fue generado antes."""
    embeddings = GoogleGenerativeAIEmbeddings(model="models/gemini-embedding-001")

    if os.path.exists(INDEX_PATH):
        return FAISS.load_local(INDEX_PATH, embeddings, allow_dangerous_deserialization=True)

    print(f"Indexando documentos desde '{DATA_DIR}' (múltiples formatos)...")
    documents = load_all_documents(DATA_DIR)

    if not documents:
        print(f"ERROR: no se encontraron documentos soportados en '{DATA_DIR}'")
        sys.exit(1)

    splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=150)
    chunks = splitter.split_documents(documents)
    print(f"Total de fragmentos generados: {len(chunks)}")

    vectorstore = FAISS.from_documents(chunks, embeddings)
    vectorstore.save_local(INDEX_PATH)
    return vectorstore


def build_agent():
    """Construye la cadena de preguntas y respuestas (RetrievalQA) con Gemini."""
    vectorstore = build_or_load_index()
    retriever = vectorstore.as_retriever(search_kwargs={"k": 4})

    llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash", temperature=0)

    qa_chain = RetrievalQA.from_chain_type(
        llm=llm,
        chain_type="stuff",
        retriever=retriever,
        return_source_documents=True,
    )
    return qa_chain


def ask(agent, question: str) -> str:
    result = agent.invoke({"query": question})
    return result["result"]


if __name__ == "__main__":
    if not os.environ.get("GOOGLE_API_KEY"):
        print("ERROR: definí la variable de entorno GOOGLE_API_KEY con tu clave de Gemini.")
        sys.exit(1)

    print("Construyendo el agente (esto puede tardar unos segundos la primera vez)...")
    agent = build_agent()
    print("Agente listo. Escribí tu pregunta (o 'salir' para terminar).\n")

    while True:
        question = input("Pregunta: ").strip()
        if question.lower() in ("salir", "exit", "quit"):
            break
        if not question:
            continue
        respuesta = ask(agent, question)
        print(f"\nRespuesta: {respuesta}\n")