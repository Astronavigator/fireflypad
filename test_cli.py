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

    # Embeddings command - show embeddings for a note
    embeddings_parser = subparsers.add_parser("embeddings")
    embeddings_parser.add_argument("note_id", type=int, help="Note ID to show embeddings for")

    args = parser.parse_args()
    manager = NoteManager()

    # Set up logging callback to see progress
    def log_callback(message: str, is_chunk: bool = False):
        if not is_chunk:
            logger.info(message)
        else:
            # For streaming chunks, print on same line
            print(message, end='', flush=True)

    manager.set_log_callback(log_callback)

    if args.command == "add":
        await manager.add_note_async(args.text)
        # Wait for queue to process completely
        await manager.queue.join()
        logger.info("Note added successfully")

    elif args.command == "find":
        logger.info(f"Searching for: {args.query}")
        try:
            results = manager.find_notes(args.query)
            logger.info(f"Found {len(results)} results:")
            for r in results:
                note_id, content, tags, distance = r
                tags_str = ", ".join(tags) if tags else "none"
                logger.info(f"ID {note_id}: {content} (Tags: {tags_str}) [Dist: {distance:.4f}]")
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
            logger.info(f"Showing last {len(notes)} notes:")
            for note_id, content, tags in notes:
                tags_str = ", ".join(tags) if tags else "none"
                logger.info(f"ID {note_id}: {content} (Tags: {tags_str})")
        except Exception as e:
            logger.exception(f"List failed: {e}")

    elif args.command == "embeddings":
        try:
            embeddings = manager.db.get_note_embeddings(args.note_id)
            logger.info(f"Note {args.note_id} has {len(embeddings)} embeddings:")
            for emb_id, text, kind, _ in embeddings:
                logger.info(f"  [{kind}] ID {emb_id}: {text[:50]}...")
        except Exception as e:
            logger.exception(f"Failed to get embeddings: {e}")

    else:
        parser.print_help()


if __name__ == "__main__":
    asyncio.run(main())
