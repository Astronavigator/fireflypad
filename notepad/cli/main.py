#! python
import asyncio
from prompt_toolkit import PromptSession
from prompt_toolkit.auto_suggest import AutoSuggest
from prompt_toolkit.history import InMemoryHistory
from notepad.core.manager import NoteManager
from notepad.cli.cli_adapter import CLIAdapter
from notepad.utils.commands import command_registry, InputMode

async def main():
    manager = NoteManager()
    cli_adapter = CLIAdapter(manager)
    session = PromptSession(history=InMemoryHistory())

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

            # Parse input using command registry
            mode, command_name, argument = command_registry.parse_input(user_input)
            
            if mode == InputMode.COMMAND_ONLY:
                # $$ prefix - must be a command
                if command_name:
                    is_valid, error_msg = command_registry.validate_command(command_name, argument)
                    if is_valid:
                        result = await cli_adapter.execute_command(command_name, argument)
                        if result.strip():
                            print(f"\n{result}\n")
                        else:
                            print("\n")
                    else:
                        print(f"Error: {error_msg}")
                else:
                    print("Error: $$ requires a command")
            
            elif mode == InputMode.COMMAND_OR_AI:
                # $ prefix - command or AI chat
                if command_name and command_registry.is_command(command_name):
                    # It's a command
                    is_valid, error_msg = command_registry.validate_command(command_name, argument)
                    if is_valid:
                        result = await cli_adapter.execute_command(command_name, argument)
                        if result.strip():
                            print(f"\n{result}\n")
                        else:
                            print("\n")
                    else:
                        print(f"Error: {error_msg}")
                else:
                    # It's AI chat
                    response = await cli_adapter.handle_ai_chat(user_input)
                    print(f"AI: {response}\n")
            
            elif mode == InputMode.COMMAND_OR_NOTE:
                # No prefix - command or note
                if command_name and command_registry.is_command(command_name):
                    # It's a command
                    is_valid, error_msg = command_registry.validate_command(command_name, argument)
                    if is_valid:
                        result = await cli_adapter.execute_command(command_name, argument)
                        if result.strip():
                            print(f"\n{result}\n")
                        else:
                            print("\n")
                    else:
                        print(f"Error: {error_msg}")
                else:
                    # It's a note
                    print(f"Me: {user_input}")
                    result = await cli_adapter.handle_note_addition(user_input)
                    print(f"{result}\n")

        except (KeyboardInterrupt, EOFError):
            break
        except Exception as e:
            print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(main())
