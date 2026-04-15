import unittest
from unittest.mock import Mock, patch
import json
from ollama_client import OllamaClient


class TestOllamaClientAnalyzeNote(unittest.TestCase):
    
    def setUp(self):
        """Set up test fixtures before each test method."""
        self.client = OllamaClient()
    
    def test_analyze_note_structure_success(self):
        """Test that analyze_note returns correct structure when extraction succeeds."""
        # Mock response from extract_tag
        mock_json_response = '{"questions": ["What is Python?", "How to use lists?"], "tags": ["programming", "tutorial"]}'
        
        with patch.object(self.client, 'extract_tag', return_value=mock_json_response):
            result = self.client.analyze_note("Python is a programming language with lists and data structures.")
            
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
    
    def test_analyze_note_structure_empty_json(self):
        """Test that analyze_note returns empty structure when JSON is empty."""
        mock_json_response = '{"questions": [], "tags": []}'
        
        with patch.object(self.client, 'extract_tag', return_value=mock_json_response):
            result = self.client.analyze_note("Some simple text.")
            
            # Check structure
            self.assertIsInstance(result, dict)
            self.assertIn('questions', result)
            self.assertIn('tags', result)
            
            # Check that all lists are empty
            self.assertEqual(result['questions'], [])
            self.assertEqual(result['tags'], [])
    
    def test_analyze_note_extraction_failure(self):
        """Test that analyze_note returns empty structure when extract_tag fails."""
        with patch.object(self.client, 'extract_tag', return_value=None):
            result = self.client.analyze_note("Some text that won't be processed.")
            
            # Check structure
            self.assertIsInstance(result, dict)
            self.assertIn('questions', result)
            self.assertIn('tags', result)
            
            # Check that all lists are empty (fallback case)
            self.assertEqual(result['questions'], [])
            self.assertEqual(result['tags'], [])
    
    def test_analyze_note_invalid_json(self):
        """Test that analyze_note handles invalid JSON gracefully."""
        mock_invalid_json = '{"questions": ["test"], "tags": ["test"], invalid json'
        
        with patch.object(self.client, 'extract_tag', return_value=mock_invalid_json):
            with self.assertRaises(json.JSONDecodeError):
                self.client.analyze_note("Some text.")
    
    def test_analyze_note_with_various_content_types(self):
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
                with patch.object(self.client, 'extract_tag', return_value=mock_json_response):
                    result = self.client.analyze_note(text)
                    
                    # Always return correct structure regardless of input
                    self.assertIsInstance(result, dict)
                    self.assertIn('questions', result)
                    self.assertIn('tags', result)
                    self.assertIsInstance(result['questions'], list)
                    self.assertIsInstance(result['tags'], list)
    
    def test_analyze_note_prompt_construction(self):
        """Test that the prompt is constructed correctly with the note text."""
        test_text = "This is a test note about programming."
        
        with patch.object(self.client, 'extract_tag') as mock_extract:
            mock_extract.return_value = '{"questions": [], "tags": []}'
            
            self.client.analyze_note(test_text)
            
            # Check that extract_tag was called with the correct tag
            mock_extract.assert_called_once()
            call_args = mock_extract.call_args
            self.assertEqual(call_args[0][1], "result")  # tag parameter
            
            # Check that the prompt contains the note text
            prompt = call_args[0][0]  # text parameter
            self.assertIn(test_text, prompt)
            self.assertIn("<note>", prompt)
            self.assertIn("</note>", prompt)
            self.assertIn("Проанализируй эту заметку", prompt)


if __name__ == '__main__':
    unittest.main()
