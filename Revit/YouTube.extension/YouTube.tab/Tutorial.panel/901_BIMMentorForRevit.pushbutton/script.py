"""Revit Usage Chatbox - AI Revit Assistant.
A beginner-friendly AI usage assistant for Revit with local RAG support.
"""

from pyrevit import revit, script, forms
import wpf
from System import Windows
import json
import os
import System
from System.Net import WebClient, ServicePointManager, SecurityProtocolType
from System.Text import Encoding

# --- [ IRONPYTHON HTTP COMPATIBILITY ] ---
# Manually enable TLS 1.2 for modern API connections
ServicePointManager.SecurityProtocol = SecurityProtocolType.Tls12

class RequestsWrapper:
    """A minimal 'requests' replacement using .NET WebClient for IronPython."""
    class Response:
        def __init__(self, status_code, text):
            self.status_code = status_code
            self.text = text
        def json(self):
            return json.loads(self.text)

    def post(self, url, json=None, headers=None, timeout=30):
        # Use simple mapping to avoid shadowing the 'json' module
        json_payload = json 
        import json as json_module
        
        client = WebClient()
        if headers:
            for k, v in headers.items():
                client.Headers.Add(k, v)
        if "Content-Type" not in [str(h) for h in client.Headers]:
            client.Headers.Add("Content-Type", "application/json")
        
        try:
            body = json_module.dumps(json_payload)
            response_bytes = client.UploadData(url, "POST", Encoding.UTF8.GetBytes(body))
            return self.Response(200, Encoding.UTF8.GetString(response_bytes))
        except Exception as e:
            # Extract actual HTTP status code for fallbacks if possible
            status = 400
            error_msg = str(e)
            if "404" in error_msg: status = 404
            elif "401" in error_msg: status = 401
            elif "403" in error_msg: status = 403
            return self.Response(status, error_msg)



# Replace requests with our wrapper
requests = RequestsWrapper()


# --- [ SYSTEM PROMPT ] ---
SYSTEM_PROMPT = """You are an expert Revit Support Assistant.
Your goal is to provide concise, accurate, and helpful guidance on how to use Autodesk Revit. 
Base your answers strictly on the Revit operations manual and help documentation provided in the context below.
Describe the steps clearly (e.g. which tab to go to, which tool to click).
Maintain a professional and approachable tone.

LIMITATION: If the context does not contain the answer, politely state: 'I am sorry, I could not find specific guidance for that topic in our manual database.'"""

# --- [ VECTOR MATH HELPERS ] ---

def cosine_similarity(v1, v2):
    """Calculates similarity between two vectors."""
    dot = sum(a * b for a, b in zip(v1, v2))
    mag1 = sum(a*a for a in v1)**0.5
    mag2 = sum(a*a for a in v2)**0.5
    if not mag1 or not mag2: return 0
    return dot / (mag1 * mag2)

# --- [ AI API CALLERS ] ---

def get_query_embedding(text, api_key):
    """Gets embedding for the user's question using Gemini."""
    url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-embedding-001:embedContent?key=" + api_key
    payload = {
        "model": "models/gemini-embedding-001",
        "content": {"parts": [{"text": text}]},
        "taskType": "RETRIEVAL_QUERY"
    }
    res = requests.post(url, json=payload, timeout=10)
    if res.status_code == 200:
        return res.json()["embedding"]["values"]
    return None

def call_gemini(api_key, model, system_prompt, user_prompt):
    # Ensure model starts with 'models/' if it doesn't already
    if "/" not in model:
        model = "models/" + model
    
    # Using v1 for better stability
    url = "https://generativelanguage.googleapis.com/v1/{}:generateContent?key={}".format(model, api_key)
    
    # Universal multi-turn payload structure (Most compatible)
    payload = {
        "contents": [
            {"role": "user", "parts": [{"text": "SYSTEM INSTRUCTION: " + system_prompt}]},
            {"role": "model", "parts": [{"text": "Understood. I am your BIM Mentor AI assistant. I will strictly follow those guidelines."}]},
            {"role": "user", "parts": [{"text": user_prompt}]}
        ],
        "generationConfig": {"temperature": 0.2}
    }
    
    res = requests.post(url, json=payload, timeout=30)
    
    # Fallback to v1beta if v1 is not available for this model
    if res.status_code == 404:
        url = url.replace("/v1/", "/v1beta/")
        res = requests.post(url, json=payload, timeout=30)
        
    if res.status_code == 200:
        try:
            data = res.json()
            return data["candidates"][0]["content"]["parts"][0]["text"]
        except Exception:
            return "Gemini Format Error. Raw response: " + res.text

    return "Gemini Error ({}). Info: {}".format(res.status_code, res.text)

def call_openai(api_key, model, system_prompt, user_prompt):
    url = "https://api.openai.com/v1/chat/completions"
    headers = {"Authorization": "Bearer " + api_key, "Content-Type": "application/json"}
    payload = {
        "model": model,
        "messages": [{"role": "system", "content": system_prompt}, {"role": "user", "content": user_prompt}],
        "temperature": 0.2
    }
    response = requests.post(url, headers=headers, json=payload, timeout=30)
    if response.status_code == 200:
        return response.json()["choices"][0]["message"]["content"]
    return "OpenAI Error: " + response.text

def call_claude(api_key, model, system_prompt, user_prompt):
    url = "https://api.anthropic.com/v1/messages"
    headers = {"x-api-key": api_key, "anthropic-version": "2023-06-01", "Content-Type": "application/json"}
    payload = {
        "model": model, "system": system_prompt,
        "messages": [{"role": "user", "content": user_prompt}],
        "max_tokens": 2048, "temperature": 0.2
    }
    response = requests.post(url, headers=headers, json=payload, timeout=30)
    if response.status_code == 200:
        return response.json()["content"][0]["text"]
    return "Claude Error: " + response.text

def call_local_llm(model, system_prompt, user_prompt, custom_url=""):
    """
    Calls a local LLM (Ollama).
    Default URL: http://localhost:11434/api/generate
    """
    url = custom_url if custom_url and custom_url.startswith("http") else "http://localhost:11434/api/generate"
    
    payload = {
        "model": model if model else "llama3",
        "prompt": "{}\n\nUSER: {}".format(system_prompt, user_prompt),
        "stream": False
    }
    
    try:
        response = requests.post(url, json=payload, timeout=60)
        if response.status_code == 200:
            return response.json().get("response", "No response from Local AI.")
        return "Local AI Error: " + response.text
    except Exception as e:
        return "Connection Error: Ensure Ollama is running at {}. Error: {}".format(url, str(e))

# --- [ UI WINDOW CLASS ] ---

class RevitUsageChatboxWindow(Windows.Window):
    def __init__(self):
        wpf.LoadComponent(self, script.get_bundle_file('ui.xaml'))
        # Local storage setup
        self.env_path = os.path.join(os.path.dirname(__file__), ".env")
        self.load_settings()
        
        # Events
        self.btn_ask.Click += self.on_ask
        self.btn_clear.Click += self.on_clear
        self.btn_save_config.Click += self.on_save_config
        self.btn_browse_kb.Click += self.on_browse_kb

    def load_settings(self):
        """Load settings from local .env file."""
        data = {}
        if os.path.exists(self.env_path):
            try:
                with open(self.env_path, 'r') as f:
                    for line in f:
                        if "=" in line:
                            k, v = line.strip().split("=", 1)
                            data[k] = v
            except Exception as e:
                print("Error loading .env: " + str(e))

        self.txt_api_key.Text = data.get("API_KEY", "")
        self.txt_model.Text = data.get("MODEL", "gemini-3.1-flash-lite-preview")
        self.cmb_provider.SelectedIndex = int(data.get("PROVIDER_IDX", 0))
        self.txt_kb_path.Text = data.get("KB_PATH", "revit_knowledge.json")
        self.chk_use_rag.IsChecked = data.get("USE_RAG", "True") == "True"

    def on_save_config(self, sender, args):
        """Save current UI values to the local .env file."""
        try:
            with open(self.env_path, 'w') as f:
                f.write("API_KEY={}\n".format(self.txt_api_key.Text))
                f.write("MODEL={}\n".format(self.txt_model.Text))
                f.write("PROVIDER_IDX={}\n".format(self.cmb_provider.SelectedIndex))
                f.write("KB_PATH={}\n".format(self.txt_kb_path.Text))
                f.write("USE_RAG={}\n".format(self.chk_use_rag.IsChecked))
            forms.alert("Settings saved to local .env file!", title="Revit Usage Chatbox")
        except Exception as e:
            forms.alert("Error saving .env: " + str(e))

    def on_browse_kb(self, sender, args):
        path = forms.pick_file(file_ext='json')
        if path:
            self.txt_kb_path.Text = path

    def on_clear(self, sender, args):
        self.txt_output.Text = ""
        self.txt_input.Text = ""

    def on_ask(self, sender, args):
        user_msg = self.txt_input.Text.strip()
        if not user_msg: return
        
        api_key = self.txt_api_key.Text
        provider_idx = self.cmb_provider.SelectedIndex
        
        # Local AI (Idx 3) doesn't strictly need a 'key', 
        # but we use the field as a custom URL.
        if not api_key and provider_idx != 3:
            forms.alert("Please provide an API Key in Settings.")
            return

        # 1. RAG LOGIC: Search Knowledge Base
        context_text = ""
        if self.chk_use_rag.IsChecked:
            kb_path = self.txt_kb_path.Text
            if not os.path.isabs(kb_path):
                kb_path = os.path.join(os.path.dirname(__file__), kb_path)
            
            if os.path.exists(kb_path):
                self.txt_output.Text += "\n\n[SEARCHING KNOWLEDGE BASE...]"
                try:
                    # Get user question embedding (Need Gemini key for this)
                    q_vec = get_query_embedding(user_msg, api_key)
                    if q_vec:
                        with open(kb_path, 'r') as f:
                            kb_data = json.load(f)
                        
                        # Rank by similarity
                        for item in kb_data:
                            item['score'] = cosine_similarity(q_vec, item['vector'])
                        
                        top_items = sorted(kb_data, key=lambda x: x['score'], reverse=True)[:3]
                        
                        # Build context
                        context_parts = []
                        for item in top_items:
                            if item['score'] > 0.6: # threshold
                                context_parts.append("Source: {}\nContent: {}".format(item.get('title'), item.get('text')))
                        
                        if context_parts:
                            context_text = "\n\n---\n\n".join(context_parts)
                except Exception as e:
                    print("RAG Error: " + str(e))

        # 2. Prepare Augmented Prompt
        final_system_prompt = SYSTEM_PROMPT
        if context_text:
            final_system_prompt += "\n\nUSE THE FOLLOWING CONTEXT TO ANSWER:\n" + context_text

        # 3. Call AI
        self.txt_output.Text += "\n\nYOU: " + user_msg
        self.txt_output.Text += "\n\nAI CHATBOX: Thinking..."
        self.txt_output.ScrollToEnd()
        
        provider_idx = self.cmb_provider.SelectedIndex
        model = self.txt_model.Text.strip()
        api_key = self.txt_api_key.Text.strip()
        
        try:
            if provider_idx == 0: response = call_gemini(api_key, model, final_system_prompt, user_msg)
            elif provider_idx == 1: response = call_claude(api_key, model, final_system_prompt, user_msg)
            elif provider_idx == 2: response = call_openai(api_key, model, final_system_prompt, user_msg)
            elif provider_idx == 3: response = call_local_llm(model, final_system_prompt, user_msg, api_key)
            else: response = "Invalid provider."
            
            self.txt_output.Text = self.txt_output.Text.replace("Thinking...", response)
        except Exception as e:
            self.txt_output.Text += "\n\n[ERROR]: " + str(e)
        
        self.txt_output.ScrollToEnd()
        self.txt_input.Text = ""

if __name__ == "__main__":
    window = RevitUsageChatboxWindow()
    window.ShowDialog()
