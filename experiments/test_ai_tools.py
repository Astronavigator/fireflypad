#!/usr/bin/env python3
"""
Простой скрипт для запуска AI Tools Tester
"""

import asyncio
from ai_tools_test import AIToolsTester


async def main():
    """Запуск тестера AI tools"""
    print("Запуск тестирования AI с external tools...")
    print("Модель: gemma4:e2b")
    print("Доступные функции: getTime(), getWeatherPrediction(), addNote(str)")
    print("-" * 50)
    
    tester = AIToolsTester()
    
    # Можно добавить тестовые примеры
    test_examples = [
        "Привет! Расскажи, какое сейчас время?",
        "Какая погода ожидается сегодня?",
        "Добавь заметку: Купить молоко и хлеб",
        "Какие заметки я добавил?",
        "Покажи текущее время и прогноз погоды"
    ]
    
    print("Примеры запросов для тестирования:")
    for i, example in enumerate(test_examples, 1):
        print(f"{i}. {example}")
    
    print("\nНачинаем интерактивный чат...")
    await tester.run_interactive_chat()


if __name__ == "__main__":
    asyncio.run(main())
