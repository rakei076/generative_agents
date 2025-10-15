# Quick Reference: New vs Old API Parameters

## Parameter Mapping

| Old Parameter        | New Parameter        | Notes                                    |
|---------------------|---------------------|------------------------------------------|
| `engine`            | `model`             | Now uses "gpt-5-nano" by default         |
| `max_tokens`        | `max_output_tokens` | Same functionality, new name             |
| `temperature`       | `temperature`       | No change                                |
| `top_p`             | `top_p`             | Only included if != 1                    |
| `frequency_penalty` | ❌ REMOVED          | Not supported in new API                 |
| `presence_penalty`  | ❌ REMOVED          | Not supported in new API                 |
| `stream`            | ❌ REMOVED          | Not supported in new API                 |
| `stop` (string)     | ❌ REMOVED          | Not supported in new API                 |

## Example Transformations

### Example 1: Basic Request
```python
# OLD
gpt_param = {
    "engine": "text-davinci-003",
    "max_tokens": 50,
    "temperature": 0,
    "top_p": 1,
    "stream": False,
    "frequency_penalty": 0,
    "presence_penalty": 0,
    "stop": None
}

# NEW
gpt_param = {
    "model": "gpt-5-nano",
    "max_output_tokens": 50,
    "temperature": 0
}
```

### Example 2: With Non-Default top_p
```python
# OLD
gpt_param = {
    "engine": "text-davinci-003",
    "max_tokens": 100,
    "temperature": 0.7,
    "top_p": 0.9,
    "stream": False,
    "frequency_penalty": 0,
    "presence_penalty": 0,
    "stop": None
}

# NEW
gpt_param = {
    "model": "gpt-5-nano",
    "max_output_tokens": 100,
    "temperature": 0.7,
    "top_p": 0.9
}
```

### Example 3: High Temperature Sampling
```python
# OLD
gpt_param = {
    "engine": "text-davinci-002",
    "max_tokens": 500,
    "temperature": 1,
    "top_p": 1,
    "stream": False,
    "frequency_penalty": 0,
    "presence_penalty": 0,
    "stop": None
}

# NEW
gpt_param = {
    "model": "gpt-5-nano",
    "max_output_tokens": 500,
    "temperature": 1
}
```

## Environment Variables

### Setting Custom Model
```bash
# Use GPT-4 instead of default gpt-5-nano
export OPENAI_MODEL="gpt-4"

# Use GPT-3.5 Turbo
export OPENAI_MODEL="gpt-3.5-turbo"
```

## Running Tests

```bash
# Navigate to test directory
cd reverie/backend_server/persona/prompt_template

# Run all tests
python3 test_gpt_structure.py -v

# Run specific test class
python3 test_gpt_structure.py TestGPTRequest -v

# Run with minimal output
python3 test_gpt_structure.py
```

## Common Error Messages

### Before Migration
```
TOKEN LIMIT EXCEEDED
```
- Still works the same, but now includes better logging

### After Migration
```
ERROR: Empty response
API ERROR
TOKEN LIMIT EXCEEDED
ERROR
```
- More specific error types for better debugging
- Check logs for detailed error messages

## Quick Setup Reminder

1. Create `utils.py` in `reverie/backend_server/`:
```python
openai_api_key = "sk-your-api-key-here"
key_owner = "Your Name"

maze_assets_loc = "../../environment/frontend_server/static_dirs/assets"
env_matrix = f"{maze_assets_loc}/the_ville/matrix"
env_visuals = f"{maze_assets_loc}/the_ville/visuals"

fs_storage = "../../environment/frontend_server/storage"
fs_temp_storage = "../../environment/frontend_server/temp_storage"

collision_block_id = "32125"

debug = True
```

2. Install requirements:
```bash
pip install -r requirements.txt
```

3. (Optional) Set custom model:
```bash
export OPENAI_MODEL="gpt-4"
```

4. Run tests:
```bash
cd reverie/backend_server/persona/prompt_template
python3 test_gpt_structure.py -v
```

## Key Improvements

✅ Cleaner parameter dictionaries (fewer parameters)
✅ Automatic model normalization
✅ Better error handling and logging
✅ Comprehensive test coverage
✅ Easy model switching via environment variable
✅ No API key leakage in logs
✅ Graceful handling of empty/malformed responses

## Need Help?

1. Check `MIGRATION_GUIDE.md` for detailed information
2. Review test cases in `test_gpt_structure.py` for examples
3. Check logs with `debug=True` in `utils.py`
