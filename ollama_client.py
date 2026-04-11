import ollama
from config import EMBEDDING_MODEL, AI_MODEL

class OllamaClient:
    def __init__(self, embed_model=EMBEDDING_MODEL, ai_model=AI_MODEL):
        self.embed_model = embed_model
        self.ai_model = ai_model

    def get_embedding(self, text):
        response = ollama.embeddings(model=self.embed_model, prompt=text)
        return response['embedding']

    def chat(self, prompt, history=None):
        messages = []
        if history:
            messages.extend(history)
        messages.append({'role': 'user', 'content': prompt})
        
        response = ollama.chat(model=self.ai_model, messages=messages)
        return response['message']['content']

    def analyze_note(self, text):
        prompt = f"Analyze the following note and provide a short list of comma-separated tags that best describe its content. Return ONLY the tags.\n\nNote: {text}"
        return self.chat(prompt)
