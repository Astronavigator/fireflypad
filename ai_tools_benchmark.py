#!/usr/bin/env python3
"""
AI Tools Benchmark - testing module for Ollama models with tool calling
Tests gemma4:e2b and gemma4:e4b models with external functions
"""

import ollama
import datetime
from typing import Dict, Any, List


def get_time() -> str:
    """Get current time and date"""
    now = datetime.datetime.now()
    return f"Current time: {now.strftime('%H:%M:%S')}, date: {now.strftime('%d.%m.%Y')}"


def get_weather_prediction() -> str:
    """Get weather prediction for today (stub)"""
    return "Weather forecast for today: partly cloudy, temperature +18°C, west wind 5 m/s, humidity 65%"


def add_note(content: str) -> str:
    """Add a note to the notebook (stub)"""
    print(f"[TOOL CALL] addNote called with content: '{content}'")
    print(f"[TOOL CALL] Note successfully added to notebook")
    return f"Note successfully added: '{content}'"


# Available functions mapping
available_functions = {
    'get_time': get_time,
    'get_weather_prediction': get_weather_prediction,
    'add_note': add_note,
}


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
            # Use native Ollama tool calling
            response = ollama.chat(
                model=model_name,
                messages=messages,
                tools=list(available_functions.values()),
                think=False
            )
            
            messages.append(response.message)
            
            # Display thinking if available
            if response.message.get('thinking'):
                print(f"Thinking: {response.message['thinking']}")
            
            # Display content
            if response.message.get('content'):
                print(f"Response: {response.message['content']}")
            
            # Handle tool calls
            tool_calls = response.message.get('tool_calls', [])
            if tool_calls:
                print(f"Tool calls detected: {len(tool_calls)}")
                
                for call in tool_calls:
                    func_name = call.function.name
                    func_args = call.function.arguments
                    
                    print(f"  Calling {func_name} with args: {func_args}")
                    
                    # Execute the function
                    if func_name in available_functions:
                        result = available_functions[func_name](**func_args)
                        print(f"  Result: {result}")
                        
                        # Add tool result to messages
                        messages.append({
                            'role': 'tool', 
                            'tool_name': func_name, 
                            'content': result
                        })
                    else:
                        print(f"  Error: Unknown function {func_name}")
                        messages.append({
                            'role': 'tool', 
                            'tool_name': func_name, 
                            'content': f'Error: Unknown function {func_name}'
                        })
                
                # Get final response after tool execution
                final_response = ollama.chat(
                    model=model_name,
                    messages=messages,
                    think=False
                )
                
                messages.append(final_response.message)
                
                if final_response.message.get('thinking'):
                    print(f"Final thinking: {final_response.message['thinking']}")
                
                if final_response.message.get('content'):
                    print(f"Final response: {final_response.message['content']}")
            
        except Exception as e:
            print(f"ERROR: {e}")
        
        print("-" * 40)


async def main():
    """Main benchmark function"""
    print("AI Tools Benchmark")
    print("Testing Ollama models with external functions")
    print("Available functions: get_time(), get_weather_prediction(), add_note(content)")
    
    models_to_test = ['gemma4:e2b', 'gemma4:e4b']
    
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
