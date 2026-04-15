import ollama
from ollama import AsyncClient
from config import EMBEDDING_MODEL, AI_MODEL
import asyncio

class OllamaClient:
    def __init__(self, embed_model=EMBEDDING_MODEL, ai_model=AI_MODEL):
        self.embed_model = embed_model
        self.ai_model = ai_model
        self.async_client = AsyncClient()

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

    async def fake_stream(self):
        for i in range(10):
            await asyncio.sleep(0.5) # Имитация ожидания
            yield f"Токен {i} "

    async def chat_stream(self, prompt, history=None, log_callback=None):
        messages = []
        if history:
            messages.extend(history)
        messages.append({'role': 'user', 'content': prompt})
        
        stream = await self.async_client.chat(
            model=self.ai_model, 
            messages=messages, 
            stream=True,
            think=True
        )

        # async for chunk in self.fake_stream():
        #     yield chunk
        async for chunk in stream:

            if 'message' in chunk and 'thinking' in chunk['message']:
                if log_callback:
                    log_callback(chunk['message']['thinking'], is_chunk=True)
                continue
            
            if 'message' in chunk and 'content' in chunk['message']:
                if log_callback:
                    log_callback(chunk['message']['content'], is_chunk=True)
                yield chunk['message']['content']

    def analyze_note(self, text):
        prompt = f"Analyze the following note and provide a short list of comma-separated tags that best describe its content. Return ONLY the tags.\n\nNote: {text}"
        return self.chat(prompt)
