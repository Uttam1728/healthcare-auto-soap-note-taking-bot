# Prompts Directory

This directory contains all prompt templates used by the healthcare SOAP note generation system.

## Structure

```
prompts/
├── __init__.py                    # Package initialization and exports
├── basic_analysis_prompt.py       # Basic conversation analysis prompt template
├── enhanced_analysis_prompt.py    # Enhanced analysis with source mapping prompt template
├── prompt_manager.py             # PromptManager class for handling prompts
└── README.md                     # This documentation file
```

## Usage

### Using PromptManager (Recommended)

```python
from prompts import PromptManager

# For basic analysis
prompt = PromptManager.get_basic_analysis_prompt(transcript_text)

# For enhanced analysis with source mapping
prompt = PromptManager.get_enhanced_analysis_prompt(transcript_text, transcript_segments)
```

### Direct Template Import

```python
from prompts import BASIC_ANALYSIS_PROMPT_TEMPLATE, ENHANCED_ANALYSIS_PROMPT_TEMPLATE

# Format templates manually
basic_prompt = BASIC_ANALYSIS_PROMPT_TEMPLATE.format(transcript_text=transcript_text)
enhanced_prompt = ENHANCED_ANALYSIS_PROMPT_TEMPLATE.format(
    segments_text=segments_text,
    total_segments=len(segments)
)
```

## Prompt Templates

### Basic Analysis Prompt
- **File**: `basic_analysis_prompt.py`
- **Purpose**: Generates structured conversation analysis and basic SOAP notes
- **Input**: Raw conversation transcript
- **Output**: JSON with speaker analysis, conversation segments, and basic SOAP note

### Enhanced Analysis Prompt
- **File**: `enhanced_analysis_prompt.py`
- **Purpose**: Generates detailed analysis with source mapping to transcript segments
- **Input**: Numbered conversation transcript segments
- **Output**: JSON with detailed SOAP note including source references and confidence scores

## Benefits of This Structure

1. **Maintainability**: Prompts are centralized and easy to update
2. **Reusability**: Templates can be used across different services
3. **Version Control**: Changes to prompts are tracked separately from business logic
4. **Testing**: Prompts can be unit tested independently
5. **Documentation**: Each prompt template is self-documented with clear purpose

## Adding New Prompts

1. Create a new `.py` file in this directory
2. Define your prompt template as a module-level constant
3. Add appropriate documentation
4. Update `__init__.py` to export the new template
5. Consider adding methods to `PromptManager` if formatting logic is needed 