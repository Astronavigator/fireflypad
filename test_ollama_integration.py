import unittest
import time
import asyncio
from ollama_client import OllamaClient
import warnings

def async_test(func):
    """Декоратор для преобразования асинхронных тестов в синхронные"""   
    def wrapper(self, *args, **kwargs):
        loop = asyncio.new_event_loop()
        try:
            return loop.run_until_complete(func(self, *args, **kwargs))
        finally:
            # Закрываем все pending tasks
            pending = asyncio.all_tasks(loop)
            for task in pending:
                task.cancel()
            if pending:
                loop.run_until_complete(asyncio.gather(*pending, return_exceptions=True))
            loop.close()
            #sleep
            time.sleep(1)
    return wrapper


class TestOllamaIntegration(unittest.TestCase):

    def setUp(self):
        """Set up test fixtures before each test method."""
        warnings.filterwarnings("ignore", category=ResourceWarning, message="unclosed <socket.socket")
        warnings.filterwarnings("ignore", category=ResourceWarning)
        self.client = OllamaClient()
        # Add a small delay between tests to avoid overwhelming the AI model
        time.sleep(1)    
        
    
    @async_test
    async def test_analyze_note_real_ai_programming_content(self):
        """Test analyze_note with real AI for programming-related content."""
        text = "Python is a high-level programming language with dynamic typing. It supports multiple programming paradigms including procedural, object-oriented, and functional programming."
        print("Input text:", text)
        result = await self.client.analyze_note(text)
        
        # Check structure
        self.assertIsInstance(result, dict)
        self.assertIn('questions', result)
        self.assertIn('tags', result)
        
        # Check types
        self.assertIsInstance(result['questions'], list)
        self.assertIsInstance(result['tags'], list)
        
        # Check that lists are not empty (AI should generate content)
        self.assertGreater(len(result['questions']), 0, "Questions list should not be empty")
        self.assertGreater(len(result['tags']), 0, "Tags list should not be empty")
        
        # Check that content is relevant
        self.assertTrue(
            any('python' in tag.lower() or 'programming' in tag.lower() for tag in result['tags']),
            "Tags should contain Python-related terms"
        )
        
        print(f"\nProgramming Content Analysis:")
        print(f"Questions: {result['questions']}")
        print(f"Tags: {result['tags']}")

    
    @async_test
    async def test_analyze_note_real_ai_recipe_content(self):
        """Test analyze_note with real AI for recipe-related content."""
        text = "To make chocolate chip cookies: mix 2 cups flour, 1 cup butter, 3/4 cup sugar, 2 eggs, 1 tsp vanilla. Bake at 375°F for 12 minutes."
        print("Input text:", text)
        result = await self.client.analyze_note(text)
        
        # Check structure
        self.assertIsInstance(result, dict)
        self.assertIn('questions', result)
        self.assertIn('tags', result)
        
        # Check types
        self.assertIsInstance(result['questions'], list)
        self.assertIsInstance(result['tags'], list)
        
        # Check that lists are not empty
        self.assertGreater(len(result['questions']), 0, "Questions list should not be empty")
        self.assertGreater(len(result['tags']), 0, "Tags list should not be empty")
        
        # Check that content is relevant
        # self.assertTrue(
        #     any('recipe' in tag.lower() or 'bake' in tag.lower() or 'cookie' in tag.lower() 
        #         for tag in result['tags']),
        #     "Tags should contain recipe-related terms"
        # )
    
        print(f"\nRecipe Content Analysis:")
        print(f"Questions: {result['questions']}")
        print(f"Tags: {result['tags']}")

    
    @async_test
    async def test_analyze_note_real_ai_meeting_content(self):
        """Test analyze_note with real AI for meeting-related content."""

        text = "Team meeting scheduled for next Monday at 2 PM. Agenda: project timeline review, budget discussion, task assignments for Q4. Please prepare status reports."        
        print("Input text:", text)
        result = await self.client.analyze_note(text)
        print("AI Response:")
        print(result)
        
        # Check structure
        self.assertIsInstance(result, dict)
        self.assertIn('questions', result)
        self.assertIn('tags', result)
        
        # Check types
        self.assertIsInstance(result['questions'], list)
        self.assertIsInstance(result['tags'], list)
        
        # Check that lists are not empty
        self.assertGreater(len(result['questions']), 0, "Questions list should not be empty")
        self.assertGreater(len(result['tags']), 0, "Tags list should not be empty")
        
        # # Check that content is relevant
        # self.assertTrue(
        #     any('meeting' in tag.lower() or 'project' in tag.lower() or 'team' in tag.lower() 
        #         for tag in result['tags']),
        #     "Tags should contain meeting-related terms"
        # )
    
        print(f"\nMeeting Content Analysis:")
        print(f"Questions: {result['questions']}")
        print(f"Tags: {result['tags']}")
    
    @async_test
    async def test_analyze_note_real_ai_short_content(self):
        """Test analyze_note with real AI for very short content."""

        text = "Buy milk and eggs"
        print("Input text:", text)
        result = await self.client.analyze_note(text)
    
        # Check structure (should still work with short content)
        self.assertIsInstance(result, dict)
        self.assertIn('questions', result)
        self.assertIn('tags', result)
        
        # Check types
        self.assertIsInstance(result['questions'], list)
        self.assertIsInstance(result['tags'], list)
    
        print(f"\nShort Content Analysis:")
        print(f"Questions: {result['questions']}")
        print(f"Tags: {result['tags']}")
    
    @async_test
    async def test_analyze_note_real_ai_technical_content(self):
        """Test analyze_note with real AI for technical documentation."""
        text = "Docker container running nginx on port 8080. Use docker-compose.yml for multi-service deployment. Environment variables configured in .env file."
        print("Input text:", text)
        result = await self.client.analyze_note(text)
    
        # Check structure
        self.assertIsInstance(result, dict)
        self.assertIn('questions', result)
        self.assertIn('tags', result)
        
        # Check types
        self.assertIsInstance(result['questions'], list)
        self.assertIsInstance(result['tags'], list)
        
        # Check that lists are not empty
        self.assertGreater(len(result['questions']), 0, "Questions list should not be empty")
        self.assertGreater(len(result['tags']), 0, "Tags list should not be empty")
        
        # Check that content is relevant
        # self.assertTrue(
        #     any('docker' in tag.lower() or 'container' in tag.lower() or 'nginx' in tag.lower() 
        #         for tag in result['tags']),
        #     "Tags should contain Docker-related terms"
        # )
    
        print(f"\nTechnical Content Analysis:")
        print(f"Questions: {result['questions']}")
        print(f"Tags: {result['tags']}")


if __name__ == '__main__':
    # Run with more verbose output to see the print statements
    unittest.main(verbosity=2)
