import sqlite3
import struct
import json
from ollama_client import OllamaClient
from database import Database

def generate_test_data():
    db = Database("research_notes.db")
    ai = OllamaClient()

    # Groups of data
    test_groups = {
        "pizza_strong": [
            "Рецепт классической пиццы Маргарита с томатами и моцареллой",
            "Как правильно замесить тесто для итальянской пиццы",
            "Лучшие сорта сыра для приготовления пиццы в домашней печи",
            "Секреты тонкого теста для римской пиццы",
            "Температура выпекания пиццы в профессиональной печи"
        ],
        "pizza_weak": [
            "История итальянской кухни и региональные особенности",
            "Рецепт традиционной пасты Карбонара",
            "Как приготовить настоящий итальянский тирамису",
            "Лучшие винодельни Тосканы и выбор вин",
            "Сборник рецептов средиземноморской диеты"
        ],
        "noise": [
            "Команда ls -la используется для просмотра всех файлов в директории",
            "Квантовая запутанность — это явление в квантовой механике",
            "День рождения бабушки 15 мая",
            "Как настроить SSH доступ к серверу Ubuntu",
            "Свойства золотого сечения в архитектуре",
            "Синтаксис цикла for в языке Python",
            "Стоимость билетов на поезд до Владивостока",
            "Как работает блокчейн и смарт-контракты",
            "Рецепт заваривания зеленого чая пуэр",
            "Основы термодинамики и закон сохранения энергии"
        ]
    }

    print("Generating embeddings and saving notes...")
    for group_name, notes in test_groups.items():
        print(f"Processing group: {group_name}")
        for note in notes:
            embedding = ai.get_embedding(note)
            # We use database.py's add_note but specifically for our research DB
            db.add_note(note, embedding, tags=["research"])

    print("\nTest dataset created in research_notes.db")

if __name__ == "__main__":
    generate_test_data()
