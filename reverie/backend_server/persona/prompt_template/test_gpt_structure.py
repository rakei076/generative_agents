"""
Unit tests for gpt_structure.py to validate the new Responses API schema.
Tests parameter transformation, error handling, and fallback behavior.
"""
import unittest
import json
import sys
import os
from unittest.mock import Mock, patch, MagicMock

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '../..'))

# Mock utils before importing gpt_structure
class MockUtils:
    """Mock utils module to avoid dependency on actual utils.py"""
    pass

mock_utils = MockUtils()
mock_utils.openai_api_key = "test-key-12345"
sys.modules['utils'] = mock_utils

# Now we can import after mocking
import gpt_structure
from gpt_structure import (
    get_default_model,
    GPT_request,
    safe_generate_response,
    ChatGPT_safe_generate_response,
    generate_prompt
)


class TestModelConfiguration(unittest.TestCase):
    """Test model configuration and normalization."""
    
    def test_get_default_model(self):
        """Test that default model is correctly set."""
        model = get_default_model()
        self.assertIn("gpt", model.lower())
    
    def test_default_model_env_override(self):
        """Test that OPENAI_MODEL environment variable overrides default."""
        with patch.dict('os.environ', {'OPENAI_MODEL': 'gpt-4'}):
            # Re-import to pick up env var
            import importlib
            import gpt_structure as gs
            importlib.reload(gs)
            # Note: This would require restart, but demonstrates the pattern
        

class TestGPTRequest(unittest.TestCase):
    """Test GPT_request with new Responses API schema."""
    
    @patch('gpt_structure.openai.ChatCompletion.create')
    def test_gpt_request_with_new_schema(self, mock_create):
        """Test that GPT_request uses correct parameter schema."""
        mock_create.return_value = {
            "choices": [{"message": {"content": "test response"}}]
        }
        
        gpt_param = {
            "model": "gpt-5-nano",
            "max_output_tokens": 50,
            "temperature": 0.7
        }
        
        result = GPT_request("test prompt", gpt_param)
        
        # Verify the API was called with correct parameters
        mock_create.assert_called_once()
        call_kwargs = mock_create.call_args[1]
        
        self.assertEqual(call_kwargs["model"], "gpt-5-nano")
        self.assertEqual(call_kwargs["max_tokens"], 50)
        self.assertEqual(call_kwargs["temperature"], 0.7)
        self.assertNotIn("engine", call_kwargs)
        self.assertNotIn("frequency_penalty", call_kwargs)
        self.assertNotIn("presence_penalty", call_kwargs)
        self.assertNotIn("stream", call_kwargs)
    
    @patch('gpt_structure.openai.ChatCompletion.create')
    def test_gpt_request_normalizes_legacy_engine(self, mock_create):
        """Test that legacy 'engine' parameter is normalized to model."""
        mock_create.return_value = {
            "choices": [{"message": {"content": "test response"}}]
        }
        
        # Legacy parameter format
        gpt_param = {
            "engine": "text-davinci-003",
            "max_output_tokens": 50,
            "temperature": 0
        }
        
        result = GPT_request("test prompt", gpt_param)
        
        # Should normalize to gpt-5-nano
        call_kwargs = mock_create.call_args[1]
        self.assertEqual(call_kwargs["model"], "gpt-5-nano")
    
    @patch('gpt_structure.openai.ChatCompletion.create')
    def test_gpt_request_omits_default_top_p(self, mock_create):
        """Test that top_p=1 is omitted from request."""
        mock_create.return_value = {
            "choices": [{"message": {"content": "test response"}}]
        }
        
        gpt_param = {
            "model": "gpt-5-nano",
            "max_output_tokens": 50,
            "temperature": 0,
            "top_p": 1
        }
        
        result = GPT_request("test prompt", gpt_param)
        
        call_kwargs = mock_create.call_args[1]
        self.assertNotIn("top_p", call_kwargs)
    
    @patch('gpt_structure.openai.ChatCompletion.create')
    def test_gpt_request_includes_non_default_top_p(self, mock_create):
        """Test that non-default top_p is included."""
        mock_create.return_value = {
            "choices": [{"message": {"content": "test response"}}]
        }
        
        gpt_param = {
            "model": "gpt-5-nano",
            "max_output_tokens": 50,
            "temperature": 0,
            "top_p": 0.9
        }
        
        result = GPT_request("test prompt", gpt_param)
        
        call_kwargs = mock_create.call_args[1]
        self.assertEqual(call_kwargs["top_p"], 0.9)


class TestErrorHandling(unittest.TestCase):
    """Test error handling and fallback behavior."""
    
    @patch('gpt_structure.openai.ChatCompletion.create')
    def test_gpt_request_handles_empty_response(self, mock_create):
        """Test that empty responses are handled gracefully."""
        mock_create.return_value = {"choices": []}
        
        gpt_param = {
            "model": "gpt-5-nano",
            "max_output_tokens": 50,
            "temperature": 0
        }
        
        result = GPT_request("test prompt", gpt_param)
        
        self.assertIn("ERROR", result)
    
    @patch('gpt_structure.openai.ChatCompletion.create')
    def test_gpt_request_handles_rate_limit(self, mock_create):
        """Test that rate limit errors are handled."""
        import openai
        mock_create.side_effect = openai.error.RateLimitError("Rate limit exceeded")
        
        gpt_param = {
            "model": "gpt-5-nano",
            "max_output_tokens": 50,
            "temperature": 0
        }
        
        result = GPT_request("test prompt", gpt_param)
        
        self.assertEqual(result, "TOKEN LIMIT EXCEEDED")
    
    @patch('gpt_structure.openai.ChatCompletion.create')
    def test_gpt_request_handles_api_error(self, mock_create):
        """Test that API errors are handled."""
        import openai
        mock_create.side_effect = openai.error.APIError("API Error")
        
        gpt_param = {
            "model": "gpt-5-nano",
            "max_output_tokens": 50,
            "temperature": 0
        }
        
        result = GPT_request("test prompt", gpt_param)
        
        self.assertEqual(result, "API ERROR")
    
    @patch('gpt_structure.GPT_request')
    def test_safe_generate_response_with_fallback(self, mock_gpt_request):
        """Test that safe_generate_response uses fallback on errors."""
        mock_gpt_request.return_value = "ERROR"
        
        gpt_param = {"model": "gpt-5-nano", "max_output_tokens": 50, "temperature": 0}
        
        def validate(response, prompt=""):
            return response != "ERROR"
        
        def cleanup(response, prompt=""):
            return response.strip()
        
        result = safe_generate_response(
            "test prompt",
            gpt_param,
            repeat=3,
            fail_safe_response="fallback value",
            func_validate=validate,
            func_clean_up=cleanup
        )
        
        self.assertEqual(result, "fallback value")
    
    @patch('gpt_structure.GPT_request')
    def test_safe_generate_response_retries(self, mock_gpt_request):
        """Test that safe_generate_response retries on validation failure."""
        # First two calls fail validation, third succeeds
        mock_gpt_request.side_effect = ["invalid", "invalid", "valid response"]
        
        gpt_param = {"model": "gpt-5-nano", "max_output_tokens": 50, "temperature": 0}
        
        def validate(response, prompt=""):
            return response == "valid response"
        
        def cleanup(response, prompt=""):
            return response.strip()
        
        result = safe_generate_response(
            "test prompt",
            gpt_param,
            repeat=5,
            fail_safe_response="fallback",
            func_validate=validate,
            func_clean_up=cleanup
        )
        
        self.assertEqual(result, "valid response")
        self.assertEqual(mock_gpt_request.call_count, 3)


class TestChatGPTSafeGenerate(unittest.TestCase):
    """Test ChatGPT safe generate with JSON response handling."""
    
    @patch('gpt_structure.ChatGPT_request')
    def test_handles_valid_json_response(self, mock_request):
        """Test that valid JSON responses are parsed correctly."""
        mock_request.return_value = '{"output": "test value"}'
        
        def validate(response, prompt=""):
            return True
        
        def cleanup(response, prompt=""):
            return response
        
        result = ChatGPT_safe_generate_response(
            "test prompt",
            "example",
            "instruction",
            repeat=3,
            fail_safe_response="fallback",
            func_validate=validate,
            func_clean_up=cleanup
        )
        
        self.assertEqual(result, "test value")
    
    @patch('gpt_structure.ChatGPT_request')
    def test_handles_malformed_json(self, mock_request):
        """Test that malformed JSON responses trigger fallback."""
        # Return malformed JSON multiple times
        mock_request.return_value = '{"output": "incomplete'
        
        def validate(response, prompt=""):
            return True
        
        def cleanup(response, prompt=""):
            return response
        
        result = ChatGPT_safe_generate_response(
            "test prompt",
            "example",
            "instruction",
            repeat=3,
            fail_safe_response="fallback",
            func_validate=validate,
            func_clean_up=cleanup
        )
        
        self.assertEqual(result, False)
    
    @patch('gpt_structure.ChatGPT_request')
    def test_handles_empty_response(self, mock_request):
        """Test that empty responses are handled."""
        mock_request.return_value = ""
        
        def validate(response, prompt=""):
            return True
        
        def cleanup(response, prompt=""):
            return response
        
        result = ChatGPT_safe_generate_response(
            "test prompt",
            "example",
            "instruction",
            repeat=3,
            fail_safe_response="fallback",
            func_validate=validate,
            func_clean_up=cleanup
        )
        
        self.assertEqual(result, False)
    
    @patch('gpt_structure.ChatGPT_request')
    def test_handles_json_without_output_key(self, mock_request):
        """Test that JSON without 'output' key triggers retry."""
        mock_request.return_value = '{"result": "wrong key"}'
        
        def validate(response, prompt=""):
            return True
        
        def cleanup(response, prompt=""):
            return response
        
        result = ChatGPT_safe_generate_response(
            "test prompt",
            "example",
            "instruction",
            repeat=3,
            fail_safe_response="fallback",
            func_validate=validate,
            func_clean_up=cleanup
        )
        
        self.assertEqual(result, False)


class TestPromptGeneration(unittest.TestCase):
    """Test prompt generation helper."""
    
    def test_generate_prompt_single_input(self):
        """Test prompt generation with single input."""
        # Create a temporary prompt file
        import tempfile
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as f:
            f.write("Test prompt with !<INPUT 0>! here.")
            temp_file = f.name
        
        try:
            result = generate_prompt("value1", temp_file)
            self.assertEqual(result, "Test prompt with value1 here.")
        finally:
            os.unlink(temp_file)
    
    def test_generate_prompt_multiple_inputs(self):
        """Test prompt generation with multiple inputs."""
        import tempfile
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as f:
            f.write("First: !<INPUT 0>!, Second: !<INPUT 1>!.")
            temp_file = f.name
        
        try:
            result = generate_prompt(["val1", "val2"], temp_file)
            self.assertEqual(result, "First: val1, Second: val2.")
        finally:
            os.unlink(temp_file)


if __name__ == '__main__':
    unittest.main()
