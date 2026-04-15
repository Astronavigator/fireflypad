import unittest
from unittest.mock import Mock, patch, AsyncMock
import json
import asyncio
from ollama_client import OllamaClient

def async_test(func):
    """Декоратор для преобразования асинхронных тестов в синхронные"""
    async def async_wrapper(self, *args, **kwargs):
        try:
            return await func(self, *args, **kwargs)
        finally:
            # Закрываем соединения если есть метод close
            if hasattr(self, 'client') and hasattr(self.client, 'close'):
                await self.client.close()
    
    def wrapper(self, *args, **kwargs):
        loop = asyncio.new_event_loop()
        try:
            return loop.run_until_complete(async_wrapper(self, *args, **kwargs))
        finally:
            # Закрываем все pending tasks
            pending = asyncio.all_tasks(loop)
            for task in pending:
                task.cancel()
            if pending:
                loop.run_until_complete(asyncio.gather(*pending, return_exceptions=True))
            loop.close()
    return wrapper


class TestOllamaClientAnalyzeNote(unittest.TestCase):
    
    def setUp(self):
        """Set up test fixtures before each test method."""
        self.client = OllamaClient()
    
    @async_test
    async def test_analyze_note_structure_success(self):
        """Test that analyze_note returns correct structure when extraction succeeds."""
        # Mock response from extract_tag
        mock_json_response = '{"questions": ["What is Python?", "How to use lists?"], "tags": ["programming", "tutorial"]}'
        
        with patch.object(self.client, 'ask_async', new_callable=AsyncMock, return_value="<result>" + mock_json_response + "</result>"):
            with patch.object(self.client, 'extract_tag', return_value=mock_json_response):
                result = await self.client.analyze_note("Python is a programming language with lists and data structures.")
                
                # Check structure
                self.assertIsInstance(result, dict)
                self.assertIn('questions', result)
                self.assertIn('tags', result)
                
                # Check types
                self.assertIsInstance(result['questions'], list)
                self.assertIsInstance(result['tags'], list)
                
                # Check content
                self.assertEqual(result['questions'], ["What is Python?", "How to use lists?"])
                self.assertEqual(result['tags'], ["programming", "tutorial"])
    
    @async_test
    async def test_analyze_note_structure_empty_json(self):
        """Test that analyze_note returns empty structure when JSON is empty."""
        mock_json_response = '{"questions": [], "tags": []}'
        
        with patch.object(self.client, 'ask_async', new_callable=AsyncMock, return_value="<result>" + mock_json_response + "</result>"):
            with patch.object(self.client, 'extract_tag', return_value=mock_json_response):
                result = await self.client.analyze_note("Some simple text.")
                
                # Check structure
                self.assertIsInstance(result, dict)
                self.assertIn('questions', result)
                self.assertIn('tags', result)
                
                # Check that all lists are empty
                self.assertEqual(result['questions'], [])
                self.assertEqual(result['tags'], [])
    
    @async_test
    async def test_analyze_note_extraction_failure(self):
        """Test that analyze_note returns empty structure when extract_tag fails."""
        with patch.object(self.client, 'ask_async', new_callable=AsyncMock, return_value="Some response without proper tags"):
            with patch.object(self.client, 'extract_tag', return_value=None):
                result = await self.client.analyze_note("Some text that won't be processed.")
                
                # Check structure
                self.assertIsInstance(result, dict)
                self.assertIn('questions', result)
                self.assertIn('tags', result)
                
                # Check that all lists are empty (fallback case)
                self.assertEqual(result['questions'], [])
                self.assertEqual(result['tags'], [])
    
    @async_test
    async def test_analyze_note_invalid_json(self):
        """Test that analyze_note handles invalid JSON gracefully."""
        mock_invalid_json = '{"questions": ["test"], "tags": ["test"], invalid json'
        
        with patch.object(self.client, 'ask_async', new_callable=AsyncMock, return_value="<result>" + mock_invalid_json + "</result>"):
            with patch.object(self.client, 'extract_tag', return_value=mock_invalid_json):
                with self.assertRaises(json.JSONDecodeError):
                    await self.client.analyze_note("Some text.")
    
    @async_test
    async def test_analyze_note_with_various_content_types(self):
        """Test analyze_note with different types of input content."""
        test_cases = [
            "Meeting notes: Discuss project timeline, budget, and team assignments.",
            "Recipe: Mix flour, eggs, and milk. Bake at 350°F for 30 minutes.",
            "Code snippet: def fibonacci(n): return n if n <= 1 else fibonacci(n-1) + fibonacci(n-2)",
            "Personal diary: Today I felt happy and accomplished my goals."
        ]
        
        mock_json_response = '{"questions": ["test question"], "tags": ["test"]}'
        
        for text in test_cases:
            with self.subTest(text=text):
                with patch.object(self.client, 'ask_async', new_callable=AsyncMock, return_value="<result>" + mock_json_response + "</result>"):
                    with patch.object(self.client, 'extract_tag', return_value=mock_json_response):
                        result = await self.client.analyze_note(text)
                        
                        # Always return correct structure regardless of input
                        self.assertIsInstance(result, dict)
                        self.assertIn('questions', result)
                        self.assertIn('tags', result)
                        self.assertIsInstance(result['questions'], list)
                        self.assertIsInstance(result['tags'], list)
    
    @async_test
    async def test_analyze_note_prompt_construction(self):
        """Test that the prompt is constructed correctly with the note text."""
        test_text = "This is a test note about programming."
        
        with patch.object(self.client, 'ask_async', new_callable=AsyncMock) as mock_ask:
            mock_ask.return_value = "<result>{\"questions\": [], \"tags\": []}</result>"
            
            with patch.object(self.client, 'extract_tag') as mock_extract:
                mock_extract.return_value = '{"questions": [], "tags": []}'
                
                await self.client.analyze_note(test_text)
                
                # Check that ask_async was called
                mock_ask.assert_called_once()
                call_args = mock_ask.call_args
                prompt = call_args[0][0]  # prompt parameter
                
                # Check that the prompt contains the note text
                self.assertIn(test_text, prompt)
                self.assertIn("<note>", prompt)
                self.assertIn("</note>", prompt)
                self.assertIn("Проанализируй эту заметку", prompt)
                
                # Check that extract_tag was called with the correct tag
                mock_extract.assert_called_once()
                extract_call_args = mock_extract.call_args
                self.assertEqual(extract_call_args[0][1], "result")  # tag parameter


if __name__ == '__main__':
    unittest.main()
