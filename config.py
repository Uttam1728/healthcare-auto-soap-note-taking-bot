import os
from dotenv import load_dotenv

load_dotenv()

# IMPORTANT: Replace the string below with your actual API keys
# Get your Deepgram API key from: https://console.deepgram.com/
# Get your Anthropic API key from: https://console.anthropic.com/
DEEPGRAM_API_KEY = os.getenv('DEEPGRAM_API_KEY', 'REPLACE_WITH_YOUR_DEEPGRAM_API_KEY_HERE')

ANTHROPIC_API_KEY = os.getenv('ANTHROPIC_API_KEY', 'REPLACE_WITH_YOUR_ANTHROPIC_API_KEY_HERE')
# Check if API key is set
if DEEPGRAM_API_KEY == 'REPLACE_WITH_YOUR_DEEPGRAM_API_KEY_HERE':
    print("WARNING: Please set your Deepgram API key!")
    print("Either:")
    print("1. Set environment variable: export DEEPGRAM_API_KEY='your_key_here'")
    print("2. Or edit config.py and replace 'REPLACE_WITH_YOUR_DEEPGRAM_API_KEY_HERE' with your actual key") 