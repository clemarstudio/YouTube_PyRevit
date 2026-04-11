# -*- coding: utf-8 -*-
"""Revit Usage Chatbox - RAG Builder (YouTube Tutorial Version).
This script reads your "revit_operations_manual.json" and converts it 
into an AI-ready vector database using the Gemini Embedding API.
"""

import os
import json
import time
import requests

# --- [ CONFIGURATION ] ---
# Get your API key from: https://aistudio.google.com/app/apikey
GEMINI_API_KEY = "YOUR_GEMINI_API_KEY_HERE"

INPUT_FILE = "revit_operations_manual.json"
OUTPUT_FILE = "revit_knowledge.json"

cwd = os.path.dirname(__file__)
_INPUT_FILE = os.path.join(cwd, INPUT_FILE)
_OUTPUT_FILE = os.path.join(cwd, OUTPUT_FILE)

def get_embedding(text, api_key):
    """Call Google Gemini API to get a 768-dimensional vector."""
    url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-embedding-001:embedContent?key=" + api_key
    payload = {
        "model": "models/gemini-embedding-001",
        "content": {"parts": [{"text": text}]},
        "taskType": "RETRIEVAL_DOCUMENT"
    }
    try:
        response = requests.post(url, json=payload, timeout=30)
        if response.status_code == 200:
            return response.json()["embedding"]["values"]
        else:
            print(f"  ❌ Embedding Error: {response.text}")
            return None
    except Exception as e:
        print(f"  ❌ Connection Error: {e}")
        return None

def build_rag():
    if GEMINI_API_KEY == "YOUR_GEMINI_API_KEY_HERE":
        print("🛑 ERROR: Please set your GEMINI_API_KEY inside this script first!")
        return

    if not os.path.exists(_INPUT_FILE):
        print(f"🛑 ERROR: Input file '{INPUT_FILE}' not found. Please create it first.")
        return

    # 1. Read your company standards
    with open(_INPUT_FILE, 'r', encoding='utf-8') as f:
        source_data = json.load(f)

    print(f"🚀 Found {len(source_data)} standard topics. Starting vectorization...")
    
    knowledge_base = []

    for item in source_data:
        title = item.get("title", "Untitled")
        text = item.get("text", "")

        if not text:
            continue

        print(f"📦 Vectorizing: {title}...")

        # We can also split long text into smaller chunks here if needed
        # But for the tutorial, we'll keep it simple (one standard = one vector)
        vector = get_embedding(text, GEMINI_API_KEY)
        
        if vector:
            knowledge_base.append({
                "title": title,
                "text": text,
                "vector": vector
            })
            
        time.sleep(0.5) # Gentle throttling to stay within free tier limits

    # 2. Save the AI-ready version
    with open(_OUTPUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(knowledge_base, f, ensure_ascii=False)

    print(f"\n✅ COMPLETED!")
    print(f"Generated '{OUTPUT_FILE}' with {len(knowledge_base)} AI-ready topics.")
    print("👉 You can now run the BIM Mentor inside Revit!")

if __name__ == "__main__":
    build_rag()
