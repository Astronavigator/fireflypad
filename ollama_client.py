from http.client import responses
import ollama
from ollama import AsyncClient
from config import EMBEDDING_MODEL, AI_MODEL
import asyncio
import re
import json

class OllamaClient:
    def __init__(self, embed_model: str=EMBEDDING_MODEL, ai_model: str=AI_MODEL):
        self.embed_model = embed_model
        self.ai_model = ai_model
        self.async_client = AsyncClient()

    def get_embedding(self, text: str):
        response = ollama.embeddings(model=self.embed_model, prompt=text)
        return response['embedding']

    def ask(self, prompt: str, think: bool=False):
        response = ollama.chat(
            model=self.ai_model,
            messages=[{'role': 'user', 'content': prompt}],
            think=think
        )
        return response['message']['content']

    async def ask_async(self, prompt: str, think: bool=False, log_callback:callable=None):
        chunk_stream = self.chat_stream(prompt, think=think, log_callback=log_callback)
        response = ""
        async for chunk in chunk_stream:
            response += chunk
        return response

    def chat(self, prompt: str, history=None):
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

    async def chat_stream(self, prompt: str, history=None, log_callback:callable=None, think=False):
        messages = []
        if history:
            messages.extend(history)
        messages.append({'role': 'user', 'content': prompt})
        
        stream = await self.async_client.chat(
            model=self.ai_model, 
            messages=messages, 
            stream=True,
            think=think
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


    def extract_tag(self, text: str, tag: str):
        """
        Извлекает содержимое тега из текста
        """
        
        pattern = f'<{tag}>(.*?)</{tag}>'
        match = re.search(pattern, text, re.DOTALL)
        if match:
            return match.group(1).strip()
        return None

    async def analyze_note(self, text: str, log_callback:callable=None) -> dict:
        prompt = "Проанализируй эту заметку и " + \
        "1. Составь список потенциальных вопросов, на которые она отвечает (вопросов которые будет задвать пользователь rag системе)" + \
        "2. Составь список тэгов, к которым можно отнести эту заметку" + \
        "Ответ выдай в формате : <result>" + \
        '{"questions": ["вопрос1","вопрос2",...], "tags": ["тег1","тег2",...] } </result>' + \
        "<note>" + text + "</note>"

        resp = await self.ask_async(prompt, log_callback=log_callback)

        print(resp)

        json_str = self.extract_tag(resp, "result")
        if json_str:
            res = json.loads(json_str)
        else:
            res = {"questions": [], "tags": []}
        return res



    
