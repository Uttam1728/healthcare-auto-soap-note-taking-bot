import os
from dotenv import load_dotenv

load_dotenv()

# IMPORTANT: Replace the string below with your actual API keys
# Get your Deepgram API key from: https://console.deepgram.com/
# Get your Anthropic API key from: https://console.anthropic.com/
# DEEPGRAM_API_KEY = os.getenv('DEEPGRAM_API_KEY', 'REPLACE_WITH_YOUR_DEEPGRAM_API_KEY_HERE')
DEEPGRAM_API_KEY = '92ea4eff231614159e918913b00c84083759c362'

# ANTHROPIC_API_KEY = os.getenv('ANTHROPIC_API_KEY', 'REPLACE_WITH_YOUR_ANTHROPIC_API_KEY_HERE')
ANTHROPIC_API_KEY = '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'
# Check if API key is set
if DEEPGRAM_API_KEY == 'REPLACE_WITH_YOUR_DEEPGRAM_API_KEY_HERE':
    print("WARNING: Please set your Deepgram API key!")
    print("Either:")
    print("1. Set environment variable: export DEEPGRAM_API_KEY='your_key_here'")
    print("2. Or edit config.py and replace 'REPLACE_WITH_YOUR_DEEPGRAM_API_KEY_HERE' with your actual key") 