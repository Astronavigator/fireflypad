#!/usr/bin/env python3
"""
AI Tools Benchmark - testing module for Ollama models with tool calling
Tests gemma4:e2b and gemma4:e4b models with external functions
"""

import ollama
import datetime
import inspect
from typing import Dict, Any, List, Callable

def get_time(chat_func: Callable[[str], None] = None) -> str:
    """Get current time and date"""
    now = datetime.datetime.now()
    result = f"Current time: {now.strftime('%H:%M:%S')}, date: {now.strftime('%d.%m.%Y')}"
    if chat_func:
        chat_func(f"The current time is {result}")
    return result


def get_weather_prediction(chat_func: Callable[[str], None] = None) -> str:
    """Get weather prediction for today (stub)"""
    result = "Weather forecast for today: partly cloudy, temperature +18°C, west wind 5 m/s, humidity 65%"
    if chat_func:
        chat_func(f"Today's weather: {result}")
    return result


def add_note(content: str, chat_func: Callable[[str], None] = None) -> str:
    """Add a note to the notebook (stub)"""
    print(f"[TOOL CALL] addNote called with content: '{content}'")
    print(f"[TOOL CALL] Note successfully added to notebook")
    result = f"Note successfully added: '{content}'"
    if chat_func:
        chat_func(f"I've added your note: {content}")
    return result


def get_tool_schema(func: Callable) -> Dict[str, Any]:
    """Генерирует схему для ollama без chat_func параметра"""
    sig = inspect.signature(func)
    params = {}
    required = []
    
    for name, param in sig.parameters.items():
        if name == 'chat_func':
            continue
        
        param_info = {'type': 'string'}
        
        # Добавляем описание если есть в docstring
        if func.__doc__ and name in func.__doc__:
            # Простое извлечение описания из docstring
            lines = func.__doc__.split('\n')
            for line in lines:
                if name in line:
                    param_info['description'] = line.strip()
                    break
        
        params[name] = param_info
        
        # Проверяем обязательные параметры
        if param.default == inspect.Parameter.empty:
            required.append(name)
    
    return {
        'type': 'function',
        'function': {
            'name': func.__name__,
            'description': func.__doc__ or f"Function {func.__name__}",
            'parameters': {
                'type': 'object',
                'properties': params,
                'required': required
            }
        }
    }


# Available functions mapping
available_functions = {
    'get_time': get_time,
    'get_weather_prediction': get_weather_prediction,
    'add_note': add_note,
}

# Генерируем схемы для ollama
tool_schemas = [get_tool_schema(func) for func in available_functions.values()]


def chat(messages: List[Dict], text: str, model: str, think: bool = False) -> None:
    """Обёртка над ollama.chat, которая модифицирует messages"""
    response = ollama.chat(model=model, messages=messages, think=think)
    if response.message.get('content'):
        messages.append({'role': 'assistant', 'content': response.message['content']})
    if response.message.get('thinking'):
        print(f"Thinking: {response.message['thinking']}")


def handle_tool_calls(tool_calls: List, messages: List[Dict], model: str, chat_func: Callable[[str], None]) -> None:
    """Обработка вызовов инструментов"""
    for call in tool_calls:
        func_name = call.function.name
        func_args = call.function.arguments
        
        print(f"  Calling {func_name} with args: {func_args}")
        
        if func_name in available_functions:
            # Передаём chat функцию в tool
            result = available_functions[func_name](chat_func=chat_func, **func_args)
            print(f"  Result: {result}")
            
            messages.append({
                'role': 'tool', 
                'tool_name': func_name, 
                'content': result
            })
        else:
            error_msg = f'Error: Unknown function {func_name}'
            print(f"  {error_msg}")
            messages.append({
                'role': 'tool', 
                'tool_name': func_name, 
                'content': error_msg
            })


def chat_with_tools(model: str, messages: List[Dict], tools: List = None, think: bool = False) -> None:
    """Главная обёртка над ollama.chat с поддержкой инструментов"""
    # Если tools не переданы, используем сгенерированные схемы
    if tools is None:
        tools = tool_schemas
    
    # Создаем chat функцию для этого контекста
    def chat_func(text: str) -> None:
        chat(messages, text, model, think)
    
    # Первый вызов
    print("[ollama.chat]")
    print("Tools count:", len(tools))
    for tool in tools:
        if isinstance(tool, dict) and 'function' in tool:
            print(f"  - {tool['function']['name']}: {tool['function'].get('description', 'No description')}")
    response = ollama.chat(model=model, messages=messages, tools=tools, think=think)
    print("[/ollama.chat]")
    messages.append(response.message)
    
    # Показываем thinking и content
    if response.message.get('thinking'):
        print(f"Thinking: {response.message['thinking']}")
    
    if response.message.get('content'):
        print(f"Response: {response.message['content']}")
    
    # Обрабатываем tool calls
    tool_calls = response.message.get('tool_calls', [])
    if tool_calls:
        print(f"Tool calls detected: {len(tool_calls)}")
        handle_tool_calls(tool_calls, messages, model, chat_func)
        
        # Получаем финальный ответ после выполнения инструментов
        final_response = ollama.chat(model=model, messages=messages, think=think)
        messages.append(final_response.message)
        
        if final_response.message.get('thinking'):
            print(f"Final thinking: {final_response.message['thinking']}")
        
        if final_response.message.get('content'):
            print(f"Final response: {final_response.message['content']}")


# Test queries for each model
test_queries = [
    "What time is it now?",
    "What's the weather forecast for today?",
    "Add a note: Buy milk and bread",
    "Show me the current time and add a note about meeting at 3 PM",
    "Hello! How are you?",
    "Add a note: Call doctor tomorrow at 10 AM",
    "What's the weather like and what time is it?",
    "Create a note: Remember to water the plants",
]


async def test_model(model_name: str):
    """Test a specific model with all queries"""
    print(f"\n{'='*60}")
    print(f"Testing model: {model_name}")
    print(f"{'='*60}")
    
    for i, query in enumerate(test_queries, 1):
        print(f"\n--- Test {i}: {query} ---")
        
        messages = [{'role': 'user', 'content': query}]
        
        try:
            # Используем новую обёртку с поддержкой инструментов
            chat_with_tools(
                model=model_name,
                messages=messages,
                think=False
            )
            
        except Exception as e:
            print(f"ERROR: {e}")
        
        print("-" * 40)


async def main():
    """Main benchmark function"""
    print("AI Tools Benchmark")
    print("Testing Ollama models with external functions")
    print("Available functions: get_time(), get_weather_prediction(), add_note(content)")
    
    models_to_test = [
        'gemma4:e2b', 
    #    'gemma4:e4b'
    ]
    
    # Check which models are available
    print("\nChecking available models...")
    try:
        available_models = ollama.list()
        model_names = [model.model for model in available_models.models]
        
        for model in models_to_test[:]:  # Copy list to safely modify
            if model in model_names:
                print(f"  {model} - Available")
            else:
                print(f"  {model} - Not found, skipping...")
                models_to_test.remove(model)
    except Exception as e:
        print(f"Error checking models: {e}")
        return
    
    if not models_to_test:
        print("No models available for testing!")
        return
    
    # Test each model
    for model in models_to_test:
        await test_model(model)
    
    print(f"\n{'='*60}")
    print("Benchmark completed!")
    print(f"{'='*60}")


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
