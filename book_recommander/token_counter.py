"""
Token counter module for tracking OpenAI API token usage.
Provides utilities to count tokens and log usage statistics.
"""

import json
from pathlib import Path
from datetime import datetime
from typing import Dict, Tuple

try:
    import tiktoken
    _TIKTOKEN_AVAILABLE = True
except ImportError:
    tiktoken = None
    _TIKTOKEN_AVAILABLE = False

# Token log file path
TOKEN_LOG_FILE = Path("token_usage.json")

# Initialize encoders for different models
ENCODING_CACHE = {}

def get_encoding(model: str = "gpt-4"):
    """Get the tokenizer for a specific model."""
    if not _TIKTOKEN_AVAILABLE:
        raise RuntimeError("tiktoken is not installed; token counts are approximate.")

    if model not in ENCODING_CACHE:
        try:
            ENCODING_CACHE[model] = tiktoken.encoding_for_model(model)
        except KeyError:
            ENCODING_CACHE[model] = tiktoken.get_encoding("cl100k_base")
    return ENCODING_CACHE[model]

def count_tokens(text: str, model: str = "gpt-4") -> int:
    """
    Count the number of tokens in a text string.
    
    Args:
        text (str): The text to count tokens for
        model (str): The model name (for selecting appropriate tokenizer)
        
    Returns:
        int: Number of tokens
    """
    try:
        encoding = get_encoding(model)
        return len(encoding.encode(text))
    except Exception:
        return max(1, len(text.split()))

def count_messages_tokens(messages: list, model: str = "gpt-4") -> int:
    """
    Count tokens in a list of messages (for chat models).
    
    Args:
        messages (list): List of message dictionaries with 'role' and 'content'
        model (str): The model name
        
    Returns:
        int: Number of tokens
    """
    encoding = get_encoding(model)
    token_count = 0
    
    for message in messages:
        token_count += 4  # Every message has 4 tokens of overhead
        for key, value in message.items():
            if isinstance(value, str):
                token_count += len(encoding.encode(value))
    
    token_count += 2  # Final message has 2 extra tokens
    return token_count

def estimate_completion_tokens(prompt_tokens: int, output_words: int) -> int:
    """
    Estimate completion tokens based on output word count.
    Rough estimate: ~1.3 tokens per word
    
    Args:
        prompt_tokens (int): Number of input tokens
        output_words (int): Estimated number of words in output
        
    Returns:
        int: Estimated completion tokens
    """
    return max(1, int(output_words * 1.3))

def log_token_usage(model: str, prompt_tokens: int, completion_tokens: int, endpoint: str = "chat") -> None:
    """
    Log token usage to a JSON file for tracking.
    
    Args:
        model (str): Model name used
        prompt_tokens (int): Number of tokens in the prompt
        completion_tokens (int): Number of tokens in the completion
        endpoint (str): API endpoint used (chat, embedding, image, etc.)
    """
    # Load existing log
    log_data = {}
    if TOKEN_LOG_FILE.exists():
        with open(TOKEN_LOG_FILE, "r") as f:
            log_data = json.load(f)
    
    # Initialize stats if not present
    if "stats" not in log_data:
        log_data["stats"] = {}
    
    if model not in log_data["stats"]:
        log_data["stats"][model] = {
            "total_prompt_tokens": 0,
            "total_completion_tokens": 0,
            "total_tokens": 0,
            "calls": 0,
            "endpoint": endpoint
        }
    
    # Update statistics
    log_data["stats"][model]["total_prompt_tokens"] += prompt_tokens
    log_data["stats"][model]["total_completion_tokens"] += completion_tokens
    log_data["stats"][model]["total_tokens"] += prompt_tokens + completion_tokens
    log_data["stats"][model]["calls"] += 1
    log_data["stats"][model]["last_updated"] = datetime.now().isoformat()
    
    # Save updated log
    with open(TOKEN_LOG_FILE, "w") as f:
        json.dump(log_data, f, indent=2)

def get_token_usage() -> Dict:
    """
    Retrieve overall token usage statistics.
    
    Returns:
        Dict: Token usage statistics per model
    """
    if not TOKEN_LOG_FILE.exists():
        return {"stats": {}, "total": 0}
    
    with open(TOKEN_LOG_FILE, "r") as f:
        log_data = json.load(f)
    
    total_tokens = sum(
        stats["total_tokens"] 
        for stats in log_data.get("stats", {}).values()
    )
    
    log_data["total"] = total_tokens
    return log_data

def print_token_usage() -> None:
    """Print formatted token usage statistics."""
    usage = get_token_usage()
    
    print("\n" + "="*80)
    print("📊 TOKEN USAGE STATISTICS")
    print("="*80)
    
    if not usage["stats"]:
        print("No token usage recorded yet.")
    else:
        for model, stats in usage["stats"].items():
            print(f"\n📌 Model: {model}")
            print(f"   Endpoint: {stats.get('endpoint', 'unknown')}")
            print(f"   Prompt Tokens:      {stats['total_prompt_tokens']:,}")
            print(f"   Completion Tokens:  {stats['total_completion_tokens']:,}")
            print(f"   Total Tokens:       {stats['total_tokens']:,}")
            print(f"   API Calls:          {stats['calls']}")
            if "last_updated" in stats:
                print(f"   Last Updated:       {stats['last_updated']}")
    
    print(f"\n{'='*80}")
    print(f"🎯 TOTAL TOKENS CONSUMED: {usage['total']:,}")
    print("="*80 + "\n")

def reset_token_usage() -> None:
    """Reset all token usage statistics."""
    if TOKEN_LOG_FILE.exists():
        TOKEN_LOG_FILE.unlink()
    print("✅ Token usage statistics have been reset.")
