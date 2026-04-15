import asyncio
import logging
import sys
import argparse
from manager import NoteManager

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    datefmt='%H:%M:%S'
)
logger = logging.getLogger("notes_cli")

async def main():
    parser = argparse.ArgumentParser(description="Notes CLI Test Tool")
    subparsers = parser.add_subparsers(dest="command")

    # Add command
    add_parser = subparsers.add_parser("add")
    add_parser.add_argument("text", type=str, help="Text of the note to add")

    # Find command
    find_parser = subparsers.add_parser("find")
    find_parser.add_argument("query", type=str, help="Query for vector search")

    # FindAI command
    findai_parser = subparsers.add_parser("findai")
    findai_parser.add_argument("query", type=str, help="Query for AI search")

    # List command
    list_parser = subparsers.add_parser("list")
    list_parser.add_argument("--limit", type=int, default=10)

    args = parser.parse_args()
    manager = NoteManager()

    if args.command == "add":
        logger.info(f"Attempting to add note: {args.text}")
        # We need to call the worker logic directly for testing or just run it
        # Since add_note_async uses a queue and worker, we'll simulate the worker's logic 
        # to see exactly where it fails.
        try:
            logger.info("Getting AI tags...")
            tags = await manager.ai.analyze_note(args.text)
            logger.info(f"AI Tags: {tags} (Type: {type(tags)})")
            
            logger.info("Getting embedding...")
            embedding = manager.ai.get_embedding(args.text)
            logger.info(f"Embedding size: {len(embedding)}")
            
            logger.info("Saving to database...")
            note_id = manager.db.add_note(args.text, embedding, tags)
            logger.info(f"Successfully saved! Note ID: {note_id}")
        except Exception as e:
            logger.exception(f"Failed to add note: {e}")

    elif args.command == "find":
        logger.info(f"Searching for: {args.query}")
        try:
            results = manager.find_notes(args.query)
            logger.info(f"Found {len(results)} results:")
            for r in results:
                logger.info(f"ID {r[0]}: {r[1]} (Tags: {r[2]})")
        except Exception as e:
            logger.exception(f"Search failed: {e}")

    elif args.command == "findai":
        logger.info(f"AI searching for: {args.query}")
        try:
            result = manager.find_notes_ai(args.query)
            logger.info(f"AI Result: {result}")
        except Exception as e:
            logger.exception(f"AI search failed: {e}")

    elif args.command == "list":
        try:
            notes = manager.list_notes(args.limit)
            logger.info(f"Showing last {args.limit} notes:")
            for n in notes:
                logger.info(f"ID {n[0]}: {n[1]} (Tags: {n[2]})")
        except Exception as e:
            logger.exception(f"List failed: {e}")
    else:
        parser.print_help()

if __name__ == "__main__":
    asyncio.run(main())
