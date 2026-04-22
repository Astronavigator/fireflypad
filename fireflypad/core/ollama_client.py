from http.client import responses
import ollama
from ollama import AsyncClient
from fireflypad.utils.config import EMBEDDING_MODEL, AI_MODEL
import asyncio
import re
import json
import functools
import time
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from fireflypad.utils.config import OLLAMA_URL

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
        self.async_client = AsyncClient(host=OLLAMA_URL)

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
        if log_callback:
            log_callback("Analyzing note with AI...")
            log_callback(f"prompt: {prompt}")
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
        if log_callback:
            if think and response['message']['thinking']:
                log_callback(response['message']['thinking'])
            log_callback(response['message']['content'])
        return response['message']['content']

    def chat(self, prompt: str, history=None):
        messages = []
        if history:
            messages.extend(history)
        messages.append({'role': 'user', 'content': prompt})
        
        response = ollama.chat(
            model=self.ai_model, 
            messages=messages,
            stream=True
        )
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
        prompt = """
You are an AI agent inside an intelligent notepad.
Users can add any type of information to this notepad.
Phone numbers, recipes, life thoughts, anything at all.
---
Analyze this note that the user is adding to their notepad and:

1. Create a list of potential search queries
that will help find exactly this note among others 
(i.e. queries that the user might ask the system 
when they need to find this note among many others)
The queries should be as diverse as possible in wording. Don't rephrase the same query.
2. List the topics of this note
3. Create a list of tags that can be applied to this note
4. If present, list the personal names mentioned
5. Specify 2-5 general categories for this note
6. List the objects mentioned
8. List place names, cities, streets, etc. (if any)

Don't add information that isn't in the note.

Provide the answer in this format:
<result>
{"questions": ["question1","question2",...], 
 "topics": ["topic1","topic2",...],
 "tags": ["tag1", "tag2", ...],
 "names": ["name1", "name2", ...],
 "categories": ["category1", "category2"],
 "places": ["place1", "place2"]
}
</result>
---
User note:
""" + f"<note>{text}</note>"

        resp = await self.ask_async(prompt, log_callback=log_callback)

        json_str = self.extract_tag(resp, "result")
        if json_str:
            raw_data = json.loads(json_str)
            all_tags = raw_data.get("tags", [])
            all_tags.extend(raw_data.get("names", []))
            all_tags.extend(raw_data.get("places", []))
            all_tags.extend(raw_data.get("categories", []))
            all_tags.extend(raw_data.get("topics", []))
            data = {
                "questions": raw_data.get("questions", []),
                "tags": list(set(all_tags))
            }
        else:
            data = {"questions": [], "tags": []}
        return AnalyzeNoteResult.from_dict(data)



    
