"""
Author: Joon Sung Park (joonspk@stanford.edu)

File: gpt_structure.py
Description: Wrapper functions for calling OpenAI APIs.
"""
import json
import random
import openai
import time 
import os
import logging

from utils import *

# Configure logging to avoid exposing API keys
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

openai.api_key = openai_api_key

# Model configuration - can be overridden via environment variable
DEFAULT_MODEL = os.environ.get("OPENAI_MODEL", "gpt-5-nano")

def get_default_model():
    """
    Returns the default model to use for API calls.
    Can be overridden by setting the OPENAI_MODEL environment variable.
    """
    return DEFAULT_MODEL

def temp_sleep(seconds=0.1):
  time.sleep(seconds)

def ChatGPT_single_request(prompt): 
  temp_sleep()

  completion = openai.ChatCompletion.create(
    model="gpt-3.5-turbo", 
    messages=[{"role": "user", "content": prompt}]
  )
  return completion["choices"][0]["message"]["content"]


# ============================================================================
# #####################[SECTION 1: CHATGPT-3 STRUCTURE] ######################
# ============================================================================

def GPT4_request(prompt): 
  """
  Given a prompt and a dictionary of GPT parameters, make a request to OpenAI
  server and returns the response. 
  ARGS:
    prompt: a str prompt
    gpt_parameter: a python dictionary with the keys indicating the names of  
                   the parameter and the values indicating the parameter 
                   values.   
  RETURNS: 
    a str of GPT-3's response. 
  """
  temp_sleep()

  try: 
    completion = openai.ChatCompletion.create(
    model="gpt-4", 
    messages=[{"role": "user", "content": prompt}]
    )
    return completion["choices"][0]["message"]["content"]
  
  except: 
    print ("ChatGPT ERROR")
    return "ChatGPT ERROR"


def ChatGPT_request(prompt): 
  """
  Given a prompt and a dictionary of GPT parameters, make a request to OpenAI
  server and returns the response. 
  ARGS:
    prompt: a str prompt
    gpt_parameter: a python dictionary with the keys indicating the names of  
                   the parameter and the values indicating the parameter 
                   values.   
  RETURNS: 
    a str of GPT-3's response. 
  """
  # temp_sleep()
  try: 
    completion = openai.ChatCompletion.create(
    model="gpt-3.5-turbo", 
    messages=[{"role": "user", "content": prompt}]
    )
    return completion["choices"][0]["message"]["content"]
  
  except: 
    print ("ChatGPT ERROR")
    return "ChatGPT ERROR"


def GPT4_safe_generate_response(prompt, 
                                   example_output,
                                   special_instruction,
                                   repeat=3,
                                   fail_safe_response="error",
                                   func_validate=None,
                                   func_clean_up=None,
                                   verbose=False): 
  prompt = 'GPT-3 Prompt:\n"""\n' + prompt + '\n"""\n'
  prompt += f"Output the response to the prompt above in json. {special_instruction}\n"
  prompt += "Example output json:\n"
  prompt += '{"output": "' + str(example_output) + '"}'

  if verbose: 
    logger.info("GPT-4 PROMPT")
    logger.debug(prompt[:500] + "..." if len(prompt) > 500 else prompt)

  for i in range(repeat): 
    try: 
      curr_gpt_response = GPT4_request(prompt).strip()
      
      # Guard against empty responses
      if not curr_gpt_response:
        logger.warning(f"Attempt {i+1}: Empty response from GPT-4")
        continue
      
      # Try to parse JSON response
      end_index = curr_gpt_response.rfind('}') + 1
      if end_index == 0:  # No closing brace found
        logger.warning(f"Attempt {i+1}: Malformed JSON response (no closing brace)")
        continue
        
      curr_gpt_response = curr_gpt_response[:end_index]
      
      try:
        parsed_response = json.loads(curr_gpt_response)
        if "output" not in parsed_response:
          logger.warning(f"Attempt {i+1}: JSON missing 'output' key")
          continue
        curr_gpt_response = parsed_response["output"]
      except json.JSONDecodeError as e:
        logger.warning(f"Attempt {i+1}: JSON decode error: {str(e)[:100]}")
        continue
      
      if func_validate and func_validate(curr_gpt_response, prompt=prompt): 
        if func_clean_up:
          return func_clean_up(curr_gpt_response, prompt=prompt)
        return curr_gpt_response
      
      if verbose: 
        logger.debug(f"---- repeat count: {i}")
        logger.debug(str(curr_gpt_response)[:200])
        logger.debug("~~~~")

    except Exception as e: 
      logger.warning(f"Attempt {i+1}: Unexpected error: {type(e).__name__}")
      continue

  logger.warning("GPT-4 safe response failed all attempts, returning False")
  return False


def ChatGPT_safe_generate_response(prompt, 
                                   example_output,
                                   special_instruction,
                                   repeat=3,
                                   fail_safe_response="error",
                                   func_validate=None,
                                   func_clean_up=None,
                                   verbose=False): 
  # prompt = 'GPT-3 Prompt:\n"""\n' + prompt + '\n"""\n'
  prompt = '"""\n' + prompt + '\n"""\n'
  prompt += f"Output the response to the prompt above in json. {special_instruction}\n"
  prompt += "Example output json:\n"
  prompt += '{"output": "' + str(example_output) + '"}'

  if verbose: 
    logger.info("CHAT GPT PROMPT")
    logger.debug(prompt[:500] + "..." if len(prompt) > 500 else prompt)

  for i in range(repeat): 
    try: 
      curr_gpt_response = ChatGPT_request(prompt).strip()
      
      # Guard against empty responses
      if not curr_gpt_response:
        logger.warning(f"Attempt {i+1}: Empty response from ChatGPT")
        continue
      
      # Try to parse JSON response
      end_index = curr_gpt_response.rfind('}') + 1
      if end_index == 0:  # No closing brace found
        logger.warning(f"Attempt {i+1}: Malformed JSON response (no closing brace)")
        continue
        
      curr_gpt_response = curr_gpt_response[:end_index]
      
      try:
        parsed_response = json.loads(curr_gpt_response)
        if "output" not in parsed_response:
          logger.warning(f"Attempt {i+1}: JSON missing 'output' key")
          continue
        curr_gpt_response = parsed_response["output"]
      except json.JSONDecodeError as e:
        logger.warning(f"Attempt {i+1}: JSON decode error: {str(e)[:100]}")
        continue

      # print ("---ashdfaf")
      # print (curr_gpt_response)
      # print ("000asdfhia")
      
      if func_validate and func_validate(curr_gpt_response, prompt=prompt): 
        if func_clean_up:
          return func_clean_up(curr_gpt_response, prompt=prompt)
        return curr_gpt_response
      
      if verbose: 
        logger.debug(f"---- repeat count: {i}")
        logger.debug(str(curr_gpt_response)[:200])
        logger.debug("~~~~")

    except Exception as e: 
      logger.warning(f"Attempt {i+1}: Unexpected error: {type(e).__name__}")
      continue

  logger.warning("ChatGPT safe response failed all attempts, returning False")
  return False


def ChatGPT_safe_generate_response_OLD(prompt, 
                                   repeat=3,
                                   fail_safe_response="error",
                                   func_validate=None,
                                   func_clean_up=None,
                                   verbose=False): 
  if verbose: 
    print ("CHAT GPT PROMPT")
    print (prompt)

  for i in range(repeat): 
    try: 
      curr_gpt_response = ChatGPT_request(prompt).strip()
      if func_validate(curr_gpt_response, prompt=prompt): 
        return func_clean_up(curr_gpt_response, prompt=prompt)
      if verbose: 
        print (f"---- repeat count: {i}")
        print (curr_gpt_response)
        print ("~~~~")

    except: 
      pass
  print ("FAIL SAFE TRIGGERED") 
  return fail_safe_response


# ============================================================================
# ###################[SECTION 2: ORIGINAL GPT-3 STRUCTURE] ###################
# ============================================================================

def GPT_request(prompt, gpt_parameter): 
  """
  Given a prompt and a dictionary of GPT parameters, make a request to OpenAI
  server and returns the response. 
  Updated to use the Responses API schema.
  ARGS:
    prompt: a str prompt
    gpt_parameter: a python dictionary with supported parameters:
                   - model: the model to use (defaults to gpt-5-nano)
                   - max_output_tokens: max tokens to generate
                   - temperature: sampling temperature
                   - top_p: nucleus sampling parameter (optional)
                   - top_k: top-k sampling parameter (optional)
  RETURNS: 
    a str of the model's response, or fallback on error.
  """
  temp_sleep()
  
  # Normalize model name to default if legacy engine names are used
  model = gpt_parameter.get("model", get_default_model())
  if "davinci" in model or "engine" in gpt_parameter:
    model = get_default_model()
  
  try:
    # Build request parameters for Responses API schema
    request_params = {
      "model": model,
      "messages": [{"role": "user", "content": prompt}]
    }
    
    # Add max_output_tokens if specified
    if "max_output_tokens" in gpt_parameter:
      request_params["max_tokens"] = gpt_parameter["max_output_tokens"]
    
    # Add temperature if specified
    if "temperature" in gpt_parameter:
      request_params["temperature"] = gpt_parameter["temperature"]
    
    # Add top_p if specified and needed
    if "top_p" in gpt_parameter and gpt_parameter["top_p"] != 1:
      request_params["top_p"] = gpt_parameter["top_p"]
    
    # Add top_k if specified (note: not all models support this)
    if "top_k" in gpt_parameter:
      request_params["top_k"] = gpt_parameter["top_k"]
    
    logger.debug(f"Making API request with model: {model}")
    response = openai.ChatCompletion.create(**request_params)
    
    if not response or not response.get("choices"):
      logger.warning("Empty response from API, using fallback")
      return "ERROR: Empty response"
    
    return response["choices"][0]["message"]["content"]
    
  except openai.error.RateLimitError as e:
    logger.error("Rate limit exceeded")
    return "TOKEN LIMIT EXCEEDED"
  except openai.error.APIError as e:
    logger.error(f"OpenAI API error: {str(e)[:100]}")  # Limit error message length
    return "API ERROR"
  except Exception as e:
    logger.error(f"Unexpected error in GPT request: {type(e).__name__}")
    return "ERROR"


def generate_prompt(curr_input, prompt_lib_file): 
  """
  Takes in the current input (e.g. comment that you want to classifiy) and 
  the path to a prompt file. The prompt file contains the raw str prompt that
  will be used, which contains the following substr: !<INPUT>! -- this 
  function replaces this substr with the actual curr_input to produce the 
  final promopt that will be sent to the GPT3 server. 
  ARGS:
    curr_input: the input we want to feed in (IF THERE ARE MORE THAN ONE
                INPUT, THIS CAN BE A LIST.)
    prompt_lib_file: the path to the promopt file. 
  RETURNS: 
    a str prompt that will be sent to OpenAI's GPT server.  
  """
  if type(curr_input) == type("string"): 
    curr_input = [curr_input]
  curr_input = [str(i) for i in curr_input]

  f = open(prompt_lib_file, "r")
  prompt = f.read()
  f.close()
  for count, i in enumerate(curr_input):   
    prompt = prompt.replace(f"!<INPUT {count}>!", i)
  if "<commentblockmarker>###</commentblockmarker>" in prompt: 
    prompt = prompt.split("<commentblockmarker>###</commentblockmarker>")[1]
  return prompt.strip()


def safe_generate_response(prompt, 
                           gpt_parameter,
                           repeat=5,
                           fail_safe_response="error",
                           func_validate=None,
                           func_clean_up=None,
                           verbose=False): 
  """
  Safely generate a response with retry logic and fallback handling.
  Guards against empty or malformed responses.
  """
  if verbose: 
    logger.info(f"Generating response (max attempts: {repeat})")
    logger.debug(prompt[:200] + "..." if len(prompt) > 200 else prompt)

  for i in range(repeat): 
    try:
      curr_gpt_response = GPT_request(prompt, gpt_parameter)
      
      # Guard against empty or error responses
      if not curr_gpt_response or curr_gpt_response.strip() == "":
        logger.warning(f"Attempt {i+1}: Empty response from GPT")
        continue
        
      if "ERROR" in curr_gpt_response or "LIMIT EXCEEDED" in curr_gpt_response:
        logger.warning(f"Attempt {i+1}: Error response: {curr_gpt_response}")
        if i == repeat - 1:  # Last attempt
          return fail_safe_response
        continue
      
      # Validate and clean up response
      if func_validate and func_validate(curr_gpt_response, prompt=prompt):
        if func_clean_up:
          return func_clean_up(curr_gpt_response, prompt=prompt)
        return curr_gpt_response
        
      if verbose: 
        logger.debug(f"---- repeat count: {i}, response invalid")
        logger.debug(curr_gpt_response[:200] if len(curr_gpt_response) > 200 else curr_gpt_response)
        logger.debug("~~~~")
        
    except Exception as e:
      logger.warning(f"Attempt {i+1} failed with exception: {type(e).__name__}")
      if i == repeat - 1:  # Last attempt
        break
      continue
      
  logger.warning(f"All {repeat} attempts failed, using fail-safe response")
  return fail_safe_response


def get_embedding(text, model="text-embedding-ada-002"):
  text = text.replace("\n", " ")
  if not text: 
    text = "this is blank"
  return openai.Embedding.create(
          input=[text], model=model)['data'][0]['embedding']


if __name__ == '__main__':
  # Example using new Responses API schema
  gpt_parameter = {
    "model": get_default_model(),
    "max_output_tokens": 50,
    "temperature": 0
  }
  curr_input = ["driving to a friend's house"]
  prompt_lib_file = "prompt_template/test_prompt_July5.txt"
  prompt = generate_prompt(curr_input, prompt_lib_file)

  def __func_validate(gpt_response, prompt=""): 
    if len(gpt_response.strip()) <= 1:
      return False
    if len(gpt_response.strip().split(" ")) > 1: 
      return False
    return True
  def __func_clean_up(gpt_response, prompt=""):
    cleaned_response = gpt_response.strip()
    return cleaned_response

  output = safe_generate_response(prompt, 
                                 gpt_parameter,
                                 5,
                                 "rest",
                                 __func_validate,
                                 __func_clean_up,
                                 True)

  print (output)




















