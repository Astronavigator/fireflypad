from http.client import responses
import ollama
from ollama import AsyncClient
from config import EMBEDDING_MODEL, AI_MODEL
import asyncio
import re
import json
import functools
import time
from typing import List, Dict, Any, Optional
from dataclasses import dataclass


def retry_on_exception(max_attempts: int = 3, delay: float = 0.1):
    """
    Декоратор для повторного вызова функции при возникновении исключений.
    
    Args:
        max_attempts: Максимальное количество попыток (по умолчанию 3)
        delay: Задержка между попытками в секундах (по умолчанию 0.1)
    """
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            last_exception = None
            
            for attempt in range(max_attempts):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    last_exception = e
                    if attempt < max_attempts - 1:
                        time.sleep(delay)
                    continue
            
            raise last_exception
        return wrapper
    return decorator


def async_retry_on_exception(max_attempts: int = 3, delay: float = 0.1):
    """
    Асинхронный декоратор для повторного вызова функции при возникновении исключений.
    
    Args:
        max_attempts: Максимальное количество попыток (по умолчанию 3)
        delay: Задержка между попытками в секундах (по умолчанию 0.1)
    """
    def decorator(func):
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            last_exception = None
            
            for attempt in range(max_attempts):
                try:
                    return await func(*args, **kwargs)
                except Exception as e:
                    last_exception = e
                    if attempt < max_attempts - 1:
                        await asyncio.sleep(delay)
                    continue
            
            raise last_exception
        return wrapper
    return decorator


@dataclass
class AnalyzeNoteResult:
    """Result of note analysis containing questions and tags"""
    questions: List[str]
    tags: List[str]
    
    def to_dict(self) -> Dict[str, List[str]]:
        """Convert to dictionary format for backward compatibility"""
        return {
            "questions": self.questions,
            "tags": self.tags
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'AnalyzeNoteResult':
        """Create from dictionary format"""
        return cls(
            questions=data.get("questions", []),
            tags=data.get("tags", [])
        )


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
        # Use sync ollama.chat in executor to avoid async issues
        loop = asyncio.get_running_loop()
        response = await loop.run_in_executor(
            None,
            lambda: ollama.chat(
                model=self.ai_model,
                messages=[{'role': 'user', 'content': prompt}],
                think=think
            )
        )
        return response['message']['content']

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

    @async_retry_on_exception(max_attempts=3, delay=0.5)
    async def analyze_note(self, text: str, log_callback:callable=None) -> AnalyzeNoteResult:
        prompt = "Проанализируй эту заметку и " + \
        "1. Составь список потенциальных вопросов, на которые она отвечает (вопросов которые будет задвать пользователь rag системе)" + \
        "2. Составь список тэгов, к которым можно отнести эту заметку" + \
        "Ответ выдай в формате : <result>" + \
        '{"questions": ["вопрос1","вопрос2",...], "tags": ["тег1","тег2",...] } </result>' + \
        "<note>" + text + "</note>"

        resp = await self.ask_async(prompt, log_callback=log_callback)

        json_str = self.extract_tag(resp, "result")
        if json_str:
            data = json.loads(json_str)
        else:
            data = {"questions": [], "tags": []}
        return AnalyzeNoteResult.from_dict(data)



    
