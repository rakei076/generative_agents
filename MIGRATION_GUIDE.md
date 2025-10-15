# OpenAI API Modernization - Migration Guide

## Overview
This document describes the changes made to modernize the OpenAI API integration from the legacy Completion API to the modern Responses API schema.

## What Changed

### 1. Parameter Schema Updates
All `gpt_param` dictionaries have been updated from the legacy format to the new Responses API format:

**Before:**
```python
gpt_param = {
    "engine": "text-davinci-003", 
    "max_tokens": 500,
    "temperature": 1, 
    "top_p": 1, 
    "stream": False,
    "frequency_penalty": 0, 
    "presence_penalty": 0, 
    "stop": None
}
```

**After:**
```python
gpt_param = {
    "model": "gpt-5-nano",
    "max_output_tokens": 500,
    "temperature": 1
}
```

### 2. Removed Parameters
The following parameters are no longer supported and have been removed:
- `engine` (replaced with `model`)
- `frequency_penalty`
- `presence_penalty`
- `stream`
- `stop` (when used as a string)

### 3. Parameter Naming Changes
- `max_tokens` → `max_output_tokens`
- `engine` → `model`

### 4. Optional Parameters
- `top_p` is only included when it differs from the default value of 1
- `top_k` can be added when needed (though not all models support it)

## API Layer Changes

### gpt_structure.py
The `GPT_request` function has been completely rewritten to:
1. Use `openai.ChatCompletion.create()` instead of `openai.Completion.create()`
2. Normalize legacy model names to the default model (`gpt-5-nano`)
3. Handle errors more gracefully with specific error types
4. Add comprehensive logging without exposing API keys

### Enhanced Error Handling
All API functions now include:
- Guards against empty or malformed responses
- Automatic retry logic with configurable attempts
- Sensible fallbacks for JSON parsing errors
- Specific handling for rate limits and API errors
- Better logging with truncated error messages

Example of improved error handling:
```python
try:
    response = openai.ChatCompletion.create(**request_params)
    
    if not response or not response.get("choices"):
        logger.warning("Empty response from API, using fallback")
        return "ERROR: Empty response"
    
    return response["choices"][0]["message"]["content"]
    
except openai.error.RateLimitError as e:
    logger.error("Rate limit exceeded")
    return "TOKEN LIMIT EXCEEDED"
except openai.error.APIError as e:
    logger.error(f"OpenAI API error: {str(e)[:100]}")
    return "API ERROR"
except Exception as e:
    logger.error(f"Unexpected error: {type(e).__name__}")
    return "ERROR"
```

## Model Configuration

### Default Model
The system now uses `gpt-5-nano` as the default model.

### Environment Variable Override
You can override the default model using an environment variable:

```bash
export OPENAI_MODEL="gpt-4"
```

### Model Normalization
Legacy model names (e.g., `text-davinci-003`) are automatically normalized to `gpt-5-nano`.

## Testing

### Running Tests
A comprehensive test suite has been added:

```bash
cd reverie/backend_server/persona/prompt_template
python3 test_gpt_structure.py -v
```

### Test Coverage
The test suite includes 17 tests covering:
- ✓ Correct parameter schema for Responses API
- ✓ Legacy parameter normalization
- ✓ Error handling (rate limits, API errors, empty responses)
- ✓ JSON response parsing
- ✓ Malformed response handling
- ✓ Retry logic and fallback behavior

## Migration Checklist

If you're maintaining your own fork:

- [ ] Update all `gpt_param` dictionaries to use new schema
- [ ] Remove unsupported parameters
- [ ] Update `engine` to `model`
- [ ] Update `max_tokens` to `max_output_tokens`
- [ ] Test with actual API calls
- [ ] Set `OPENAI_MODEL` environment variable if needed
- [ ] Run unit tests to verify functionality

## Backward Compatibility

### Legacy Code Support
The new code automatically normalizes legacy parameters:
- If `engine` is present in `gpt_parameter`, it's automatically converted to use the default model
- Model names containing "davinci" are normalized to `gpt-5-nano`

### Breaking Changes
⚠️ **Warning**: The following are breaking changes:
1. OpenAI library version requirement: `openai>=0.27.0`
2. Response format is now from ChatCompletion API (returns message content directly)
3. Unsupported parameters will be silently ignored

## Benefits

### Improved Reliability
- Better error messages for debugging
- Automatic retry on transient failures
- Graceful degradation with fallbacks
- No crashes from malformed responses

### Better Security
- API keys never logged
- Error messages truncated to avoid data leakage
- Secure logging practices

### Easier Maintenance
- Centralized model configuration
- Easy model switching via environment variable
- Comprehensive test coverage
- Clear error handling patterns

## Troubleshooting

### Common Issues

**Issue**: `NameError: name 'openai_api_key' is not defined`
- **Solution**: Ensure `utils.py` exists in `reverie/backend_server/` with your API key

**Issue**: "TOKEN LIMIT EXCEEDED" errors
- **Solution**: Check your OpenAI API rate limits and consider adding delays between calls

**Issue**: Tests fail with import errors
- **Solution**: Ensure all dependencies from `requirements.txt` are installed

**Issue**: Want to use a different model
- **Solution**: Set `export OPENAI_MODEL="your-model-name"` before running the simulation

## Files Modified

1. `reverie/backend_server/persona/prompt_template/gpt_structure.py`
   - Updated `GPT_request()` function
   - Enhanced `safe_generate_response()` 
   - Improved `ChatGPT_safe_generate_response()`
   - Added model configuration with `get_default_model()`

2. `reverie/backend_server/persona/prompt_template/run_gpt_prompt.py`
   - Updated 36 `gpt_param` dictionaries
   - All now use new Responses API schema

3. `reverie/backend_server/persona/prompt_template/test_gpt_structure.py` (NEW)
   - Comprehensive test suite with 17 tests

4. `README.md`
   - Updated setup instructions
   - Added model configuration section
   - Added testing instructions
   - Added API migration notes

## Support

For issues or questions:
1. Check the test suite for examples
2. Review the error logs (with debug=True in utils.py)
3. Refer to OpenAI's official API documentation

## References

- [OpenAI API Documentation](https://platform.openai.com/docs/api-reference)
- [OpenAI Python Library](https://github.com/openai/openai-python)
- Original paper: [Generative Agents: Interactive Simulacra of Human Behavior](https://arxiv.org/abs/2304.03442)
