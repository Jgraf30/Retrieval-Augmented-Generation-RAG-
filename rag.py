import os
import argparse
from langchain_community.document_loaders import TextLoader, DirectoryLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import FAISS
from dotenv import load_dotenv

load_dotenv()

def ingest(data_dir="data", store_dir="store"):
    loader = DirectoryLoader(data_dir, glob="*.txt", loader_cls=TextLoader)
    docs = loader.load()
    splitter = RecursiveCharacterTextSplitter(chunk_size=800, chunk_overlap=200)
    chunks = splitter.split_documents(docs)

    embeddings = OpenAIEmbeddings(model="text-embedding-3-small")
    vectorstore = FAISS.from_documents(chunks, embeddings)
    vectorstore.save_local(store_dir)
    print(f"[INFO] Ingested {len(chunks)} chunks into {store_dir}")

def ask(store_dir="store", q="What is in the docs?"):
    embeddings = OpenAIEmbeddings(model="text-embedding-3-small")
    vectorstore = FAISS.load_local(store_dir, embeddings, allow_dangerous_deserialization=True)
    retriever = vectorstore.as_retriever()

    docs = retriever.get_relevant_documents(q)
    print(f"[INFO] Found {len(docs)} docs for query: {q}")
    for i, d in enumerate(docs, 1):
        print(f"{i}. {d.page_content[:200]}...")

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", choices=["ingest", "ask"])
    ap.add_argument("--data", default="data")
    ap.add_argument("--store", default="store")
    ap.add_argument("--q", default="What is in the docs?")
    args = ap.parse_args()

    if args.cmd == "ingest":
        ingest(args.data, args.store)
    elif args.cmd == "ask":
        ask(args.store, args.q)
