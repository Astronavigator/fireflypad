import asyncio
from prompt_toolkit import PromptSession
from prompt_toolkit.auto_suggest import AutoSuggest
from prompt_toolkit.history import InMemoryHistory
from manager import NoteManager

async def main():
    manager = NoteManager()
    session = PromptSession(history=InMemoryHistory())
    chat_history = []

    print("--- AI Notepad ---")
    print("Commands: $$ list, $$ find <query>, $$ findai <query>")
    print("AI Chat: $ <message>")
    print("Just type and Enter to save a note.")
    print("-----------------")

    while True:
        try:
            # Display saving indicator if manager is processing
            indicator = " [Saving...]" if manager.is_processing else ""
            user_input = await session.prompt_async(f"Me{indicator} > ")
            
            if not user_input.strip():
                continue

            if user_input.startswith("$$"):
                # Handle commands
                cmd_parts = user_input[2:].strip().split(maxsplit=1)
                cmd = cmd_parts[0].lower()
                arg = cmd_parts[1] if len(cmd_parts) > 1 else None

                if cmd == "list":
                    limit = int(arg) if arg and arg.isdigit() else 10
                    notes = manager.list_notes(limit)
                    print("\n--- Recent Notes ---")
                    for n in notes:
                        print(f"ID {n[0]}: {n[1]} (Tags: {n[2]})")
                    print("--------------------\n")
                    
                elif cmd == "find":
                    if not arg:
                        print("Error: find requires a query.")
                        continue
                    results = manager.find_notes(arg)
                    print("\n--- Vector Search Results ---")
                    for r in results:
                        print(f"ID {r[0]}: {r[1]} (Tags: {r[2]})")
                    print("-----------------------------\n")
                    
                elif cmd == "findai":
                    if not arg:
                        print("Error: findai requires a query.")
                        continue
                    print("\nAI is searching...")
                    result = manager.find_notes_ai(arg)
                    print(f"AI: {result}\n")
                else:
                    print(f"Unknown command: {cmd}")

            elif user_input.startswith("$"):
                # AI Chat
                prompt = user_input[1:].strip()
                print("\nAI is thinking...")
                response = manager.ai_chat(prompt, chat_history)
                print(f"AI: {response}\n")
                # Add to session history for context
                chat_history.append({'role': 'user', 'content': prompt})
                chat_history.append({'role': 'assistant', 'content': response})
                # Keep history manageable
                if len(chat_history) > 20:
                    chat_history = chat_history[-20:]

            else:
                # Add a note
                print(f"Me: {user_input}")
                await manager.add_note_async(user_input)

        except (KeyboardInterrupt, EOFError):
            break
        except Exception as e:
            print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(main())
