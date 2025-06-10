import os
import logging
from typing import Optional
from dataclasses import dataclass
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

@dataclass
class APIConfig:
    """Configuration for API keys and endpoints"""
    deepgram_api_key: str
    anthropic_api_key: str
    
    def validate(self) -> list[str]:
        """Validate API configuration and return list of errors"""
        errors = []
        
        if not self.deepgram_api_key or self.deepgram_api_key == 'REPLACE_WITH_YOUR_DEEPGRAM_API_KEY_HERE':
            errors.append("DEEPGRAM_API_KEY is not properly configured")
            
        if not self.anthropic_api_key or self.anthropic_api_key == 'REPLACE_WITH_YOUR_ANTHROPIC_API_KEY_HERE':
            errors.append("ANTHROPIC_API_KEY is not properly configured")
            
        return errors

@dataclass
class TranscriptionConfig:
    """Configuration for transcription service"""
    model: str = "nova-2"
    language: str = "en-US"
    encoding: str = "linear16"
    sample_rate: int = 16000
    utterance_end_ms: str = "2000"
    endpointing: int = 800
    enable_diarization: bool = True
    enable_smart_format: bool = True
    enable_punctuation: bool = True
    profanity_filter: bool = False
    redact_pii: bool = False
    enable_numerals: bool = True
    
    medical_keywords: list[str] = None
    
    def __post_init__(self):
        if self.medical_keywords is None:
            self.medical_keywords = [
                "patient", "doctor", "symptoms", "diagnosis", "treatment", 
                "medication", "prescription", "mg", "ml", "blood pressure", 
                "temperature", "pain", "history", "allergies", "surgery", 
                "chronic", "acute", "vital signs", "examination"
            ]

@dataclass
class AIConfig:
    """Configuration for AI analysis"""
    model: str = "claude-3-5-sonnet-20241022"
    max_tokens: int = 2500
    temperature: float = 0.1
    timeout_seconds: int = 30

@dataclass
class AppConfig:
    """Main application configuration"""
    secret_key: str
    api: APIConfig
    transcription: TranscriptionConfig
    ai: AIConfig
    host: str = "0.0.0.0"
    port: int = 5002
    debug: bool = False
    cors_allowed_origins: str = "*"
    
    @classmethod
    def from_environment(cls) -> 'AppConfig':
        """Create configuration from environment variables"""
        api_config = APIConfig(
            deepgram_api_key=os.getenv('DEEPGRAM_API_KEY', 'REPLACE_WITH_YOUR_DEEPGRAM_API_KEY_HERE'),
            anthropic_api_key=os.getenv('ANTHROPIC_API_KEY', 'REPLACE_WITH_YOUR_ANTHROPIC_API_KEY_HERE')
        )
        
        transcription_config = TranscriptionConfig()
        ai_config = AIConfig()
        
        return cls(
            secret_key=os.getenv('SECRET_KEY', 'dev-key-change-in-production'),
            host=os.getenv('HOST', '0.0.0.0'),
            port=int(os.getenv('PORT', '5002')),
            debug=os.getenv('DEBUG', 'False').lower() == 'true',
            cors_allowed_origins=os.getenv('CORS_ALLOWED_ORIGINS', '*'),
            api=api_config,
            transcription=transcription_config,
            ai=ai_config
        )
    
    def validate(self) -> list[str]:
        """Validate all configuration and return list of errors"""
        errors = []
        
        # Validate API configuration
        errors.extend(self.api.validate())
        
        # Add other validations as needed
        if self.port < 1 or self.port > 65535:
            errors.append("PORT must be between 1 and 65535")
            
        return errors

# Global configuration instance
config = AppConfig.from_environment()

# Legacy exports for backward compatibility
DEEPGRAM_API_KEY = config.api.deepgram_api_key
ANTHROPIC_API_KEY = config.api.anthropic_api_key

def validate_configuration() -> bool:
    """Validate configuration and log any issues"""
    errors = config.validate()
    
    if errors:
        for error in errors:
            logging.error(f"Configuration error: {error}")
        
        # Print helpful messages for missing API keys
        if any("DEEPGRAM_API_KEY" in error for error in errors):
            print("WARNING: Please set your Deepgram API key!")
            print("Either:")
            print("1. Set environment variable: export DEEPGRAM_API_KEY='your_key_here'")
            print("2. Or create a .env file with DEEPGRAM_API_KEY='your_key_here'")
        
        if any("ANTHROPIC_API_KEY" in error for error in errors):
            print("WARNING: Please set your Anthropic API key!")
            print("Either:")
            print("1. Set environment variable: export ANTHROPIC_API_KEY='your_key_here'")
            print("2. Or create a .env file with ANTHROPIC_API_KEY='your_key_here'")
        
        return False
    
    return True 