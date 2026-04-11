# 🏢 Build Your Firm's Custom AI BIM Mentor

Welcome! This repository accompanies the YouTube tutorial on building a **Local Knowledge-Powered AI Assistant** directly inside Autodesk Revit.

## 🎯 The Core Selling Point: Your Company, Your Rules

Generic AI models (like ChatGPT or Claude) are incredibly smart, but they suffer from one massive flaw in the AEC industry: **They don't know your company's standards.** 
When a junior architect asks, *"How do I name a structural wall type?"*, generic AI gives a generic, generalized answer that might violate your firm's BIM Execution Plan (BEP).

**The Solution:** This project teaches you how to build a **Retrieval-Augmented Generation (RAG)** pipeline. You will learn how to feed your *own* company's BIM manuals, naming conventions, and internal wikis into a local database. When a user asks a question, the AI searches and reads your company standards *first* before synthesizing its answer.

By the end of this tutorial, you will have the foundation to **build your own proprietary company knowledge database**, accessible directly inside Revit.

---

## 🎬 Video Script Outline & Core Concepts

If you are following along with the YouTube video, here are the key concepts we cover. Use this as a reference guide:

### Concept 1: The RAG Builder (Vectorizing your Standards)
To make the AI smart about your workflows, we must convert your text standards into mathematical coordinates (Vectors).
* **The Input:** Your custom JSON data (Samples provided: `revit_operations_sample.json` and `company_standards_sample.json`).
* **The Process:** In `rag_builder.py`, we send this data to Google's Gemini API to calculate "Embeddings" (a map of the text's meaning).
* **The Output:** It generates a `revit_knowledge.json` file. Think of this as the customized 'brain' containing all your proprietary standards.

### Concept 2: The Vector Search (No Complex Databases Required)
In enterprise applications, developers use massive vector databases (like ChromaDB or Pinecone). For this tutorial, we stripped out the complexity so you can see the raw mechanics.
* **The Magic:** In `script.py`, we use a pure-math `cosine_similarity` function to instantly compare the user's typed Revit question against your `revit_knowledge.json`. 
* **The Benefit:** You learn exactly *how* AI search algorithms conceptually work under the hood without having to install and host database servers.

### Concept 3: The Prompt Injection
Once the script calculates the math and finds the most relevant rule from your company database, it dynamically injects it into the AI's "System Prompt" alongside the user's question. The AI leverages this context to give a perfect, company-specific answer.

### Concept 4: The pyRevit UI (WPF)
We use a separate `ui.xaml` file to create a clean, modern user interface. We do this to bypass the complexity of coding native Revit panels in Python, keeping the focus entirely on the AI functionality.

---

## 🛠 Prerequisites for the Tutorial

To run this tool and follow the video, you need:
1. **pyRevit** installed within Autodesk Revit.
2. **Compatible with IronPython**: Works on both Python 2.7 and Python 3 engines.
3. **API Keys**:
   - [Google Gemini API Key](https://aistudio.google.com/app/apikey) (Recommended default: `gemini-3.1-flash-lite-preview`).

---

## 🚀 Getting Started (Step-by-Step)

```bash
# Only required for running the RAG Builder script externally
pip install requests
```

### Step 2: Choose Your Knowledge Source
1. Open one of the provided samples (`revit_operations_sample.json` or `company_standards_sample.json`).
2. You can also add your own firm's standards as simple JSON entries. Each entry needs a **title** and **text**.

### Step 3: Build Your AI Knowledge Database
1. Open `rag_builder.py` in your code editor.
2. Provide your **Gemini API Key**.
3. Run the script from the command line: 
   ```bash
   python rag_builder.py
   ```
4. Verify that `revit_knowledge.json` was generated successfully in your folder.

### Step 4: Run the AI inside Revit
1. Open Revit and navigate to your pyRevit extension tab.
5. **Local Option:** To use a local model, select **Local AI (Ollama)**. You can use any model name like `llama3`.
6. If you created a knowledge base in Step 3, ensure **Use RAG** is checked.
7. Click **Save Settings** (This will create a local `.env` file in your pushbutton folder).
8. Type your question and click **Ask Mentor**!

---

## 🛡️ Privacy: Using a Local Model (Ollama)

### Model Download Guide

If you are new to running AI locally, follow these steps to get your first model running in Revit:

1. **Install Ollama:** Download and install the app from [ollama.com](https://ollama.com/).
2. **Open your Terminal:** Press `Win + R`, type `cmd`, and hit Enter.
3. **Download Llama 3:** Run the following command (this is the most recommended model for Revit tasks):
   ```bash
   ollama pull llama3
   ```
4. **Verify Your Models:** You can see your downloaded models by typing:
   ```bash
   ollama list
   ```
5. **Other Recommendations:** 
   - `ollama pull phi3` (Very fast, runs on almost any laptop)
   - `ollama pull mistral` (Excellent for complex logic)

### Step-by-Step 

For many BIM teams, data privacy is the top priority. If you don't want your project data or company standards sent to the cloud, you can run a model locally on your own hardware.

1. **Connect to Revit:** In the BIM Mentor settings, choose **Local AI (Ollama)** and set the Model Name to `llama3`.
2. **Custom URL:** If you are running Ollama on a different server or using LM Studio, you can paste the full API URL (e.g., `http://192.168.1.50:11434/api/generate`) into the **API Key / Local URL** field.



---

## 📂 Repository File Structure
- `script.py`: The main Revit AI logic (now with built-in .NET web support).
- `ui.xaml`: The modern proportional interface (3x response size).
- `rag_builder.py`: The script that vectorizes your company standards.
- `.env`: (Auto-generated) Stores your API keys locally in the pushbutton folder.
- `revit_knowledge.json`: The final AI-ready vector dataset (generated by the builder).

Happy Scripting! 🚀
