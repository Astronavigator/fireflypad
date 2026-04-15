from http.client import responses
import ollama
from ollama import AsyncClient
from config import EMBEDDING_MODEL, AI_MODEL
import asyncio
import re
import json

class OllamaClient:
    def __init__(self, embed_model=EMBEDDING_MODEL, ai_model=AI_MODEL):
        self.embed_model = embed_model
        self.ai_model = ai_model
        self.async_client = AsyncClient()

    def get_embedding(self, text):
        response = ollama.embeddings(model=self.embed_model, prompt=text)
        return response['embedding']

    def ask(self, prompt, think=False):
        response = ollama.chat(
            model=self.ai_model,
            messages=[{'role': 'user', 'content': prompt}],
            think=think
        )
        return response['message']['content']

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


    def extract_tag(self, text: str, tag: str):
        """
        Извлекает содержимое тега из текста
        """
        
        pattern = f'<{tag}>(.*?)</{tag}>'
        match = re.search(pattern, text, re.DOTALL)
        if match:
            return match.group(1).strip()
        return None

    def analyze_note(self, text) -> dict:
        prompt = "Проанализируй эту заметку и " + \
        "1. Составь список потенциальных вопросов, на которые она отвечает (вопросов которые будет задвать пользователь rag системе)" + \
        "2. Составь список тэгов, к которым можно отнести эту заметку" + \
        "Ответ выдай в формате : <result>" + \
        '{"questions": ["вопрос1","вопрос2",...], "tags": ["тег1","тег2",...] } </result>' + \
        "<note>" + text + "</note>"

        resp = self.ask(prompt)

        print(resp)

        json_str = self.extract_tag(resp, "result")
        if json_str:
            res = json.loads(json_str)
        else:
            res = {"questions": [], "tags": []}
        return res
