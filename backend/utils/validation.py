"""
Input validation and sanitization utilities for the healthcare SOAP note taking bot.
Provides comprehensive validation for all user inputs and data structures.
"""

import re
import base64
import binascii
from typing import Any, Dict, List, Optional, Union, Tuple
from datetime import datetime
import html
import json
from ..utils.exceptions import ValidationError, AudioProcessingError


class InputValidator:
    """Comprehensive input validation and sanitization"""
    
    # Maximum allowed lengths for different types of content
    MAX_TRANSCRIPT_LENGTH = 100000  # 100KB
    MAX_AUDIO_CHUNK_SIZE = 1024 * 1024  # 1MB
    MAX_SESSION_ID_LENGTH = 128
    MAX_MESSAGE_LENGTH = 10000
    
    # Regex patterns for validation
    SESSION_ID_PATTERN = re.compile(r'^[a-zA-Z0-9\-_]{8,128}$')
    AUDIO_DATA_PATTERN = re.compile(r'^[A-Za-z0-9+/=]+$')
    
    @staticmethod
    def sanitize_text(text: str, max_length: Optional[int] = None) -> str:
        """
        Sanitize text input by removing dangerous characters and limiting length.
        
        Args:
            text: Input text to sanitize
            max_length: Maximum allowed length (default: no limit)
            
        Returns:
            Sanitized text
            
        Raises:
            ValidationError: If text is invalid
        """
        if not isinstance(text, str):
            raise ValidationError("Input must be a string")
        
        # Remove null bytes and control characters (except whitespace)
        sanitized = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f-\x9f]', '', text)
        
        # HTML escape to prevent injection
        sanitized = html.escape(sanitized, quote=True)
        
        # Strip excessive whitespace
        sanitized = re.sub(r'\s+', ' ', sanitized).strip()
        
        # Check length
        if max_length and len(sanitized) > max_length:
            raise ValidationError(f"Text too long (max {max_length} characters)")
        
        return sanitized
    
    @staticmethod
    def validate_session_id(session_id: str) -> str:
        """
        Validate and sanitize session ID.
        
        Args:
            session_id: Session ID to validate
            
        Returns:
            Validated session ID
            
        Raises:
            ValidationError: If session ID is invalid
        """
        if not isinstance(session_id, str):
            raise ValidationError("Session ID must be a string")
        
        session_id = session_id.strip()
        
        if not session_id:
            raise ValidationError("Session ID cannot be empty")
        
        if len(session_id) > InputValidator.MAX_SESSION_ID_LENGTH:
            raise ValidationError(f"Session ID too long (max {InputValidator.MAX_SESSION_ID_LENGTH} characters)")
        
        if not InputValidator.SESSION_ID_PATTERN.match(session_id):
            raise ValidationError("Session ID contains invalid characters")
        
        return session_id
    
    @staticmethod
    def validate_audio_data(audio_data: str) -> bytes:
        """
        Validate and decode base64 audio data.
        
        Args:
            audio_data: Base64 encoded audio data
            
        Returns:
            Decoded audio bytes
            
        Raises:
            AudioProcessingError: If audio data is invalid
        """
        if not isinstance(audio_data, str):
            raise AudioProcessingError("Audio data must be a string")
        
        audio_data = audio_data.strip()
        
        if not audio_data:
            raise AudioProcessingError("Audio data cannot be empty")
        
        # Check for valid base64 pattern
        if not InputValidator.AUDIO_DATA_PATTERN.match(audio_data):
            raise AudioProcessingError("Audio data contains invalid base64 characters")
        
        try:
            decoded = base64.b64decode(audio_data, validate=True)
        except (binascii.Error, ValueError) as e:
            raise AudioProcessingError(f"Invalid base64 audio data: {str(e)}")
        
        if len(decoded) > InputValidator.MAX_AUDIO_CHUNK_SIZE:
            raise AudioProcessingError(f"Audio chunk too large (max {InputValidator.MAX_AUDIO_CHUNK_SIZE} bytes)")
        
        if len(decoded) == 0:
            raise AudioProcessingError("Audio data is empty after decoding")
        
        return decoded
    
    @staticmethod
    def validate_transcript(transcript: str) -> str:
        """
        Validate and sanitize transcript text.
        
        Args:
            transcript: Transcript text to validate
            
        Returns:
            Validated transcript
            
        Raises:
            ValidationError: If transcript is invalid
        """
        if not isinstance(transcript, str):
            raise ValidationError("Transcript must be a string")
        
        transcript = transcript.strip()
        
        if len(transcript) > InputValidator.MAX_TRANSCRIPT_LENGTH:
            raise ValidationError(f"Transcript too long (max {InputValidator.MAX_TRANSCRIPT_LENGTH} characters)")
        
        # Remove excessive whitespace while preserving structure
        transcript = re.sub(r'\n{3,}', '\n\n', transcript)  # Max 2 consecutive newlines
        transcript = re.sub(r' {2,}', ' ', transcript)  # Single spaces only
        
        return transcript
    
    @staticmethod
    def validate_socket_message(message: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate socket message structure and content.
        
        Args:
            message: Socket message to validate
            
        Returns:
            Validated message
            
        Raises:
            ValidationError: If message is invalid
        """
        if not isinstance(message, dict):
            raise ValidationError("Message must be a dictionary")
        
        validated = {}
        
        for key, value in message.items():
            # Validate key
            if not isinstance(key, str):
                raise ValidationError("Message keys must be strings")
            
            key = InputValidator.sanitize_text(key, max_length=100)
            
            # Validate value based on type
            if isinstance(value, str):
                validated[key] = InputValidator.sanitize_text(value, max_length=InputValidator.MAX_MESSAGE_LENGTH)
            elif isinstance(value, (int, float, bool)):
                validated[key] = value
            elif isinstance(value, dict):
                validated[key] = InputValidator.validate_socket_message(value)
            elif isinstance(value, list):
                validated[key] = [
                    InputValidator.sanitize_text(item, max_length=1000) if isinstance(item, str) else item
                    for item in value[:100]  # Limit list size
                ]
            else:
                # Convert unknown types to string and sanitize
                validated[key] = InputValidator.sanitize_text(str(value), max_length=1000)
        
        return validated
    
    @staticmethod
    def validate_json_structure(data: Union[str, Dict], max_size: int = 10 * 1024 * 1024) -> Dict[str, Any]:
        """
        Validate JSON structure and size.
        
        Args:
            data: JSON string or dictionary to validate
            max_size: Maximum size in bytes
            
        Returns:
            Validated dictionary
            
        Raises:
            ValidationError: If JSON is invalid
        """
        if isinstance(data, str):
            if len(data.encode('utf-8')) > max_size:
                raise ValidationError(f"JSON too large (max {max_size} bytes)")
            
            try:
                data = json.loads(data)
            except json.JSONDecodeError as e:
                raise ValidationError(f"Invalid JSON: {str(e)}")
        
        if not isinstance(data, dict):
            raise ValidationError("JSON must be an object/dictionary")
        
        return data


class SecurityValidator:
    """Security-focused validation utilities"""
    
    # Dangerous patterns that should be blocked
    DANGEROUS_PATTERNS = [
        re.compile(r'<script.*?</script>', re.IGNORECASE | re.DOTALL),
        re.compile(r'javascript:', re.IGNORECASE),
        re.compile(r'vbscript:', re.IGNORECASE),
        re.compile(r'onload=', re.IGNORECASE),
        re.compile(r'onerror=', re.IGNORECASE),
        re.compile(r'<iframe', re.IGNORECASE),
        re.compile(r'<object', re.IGNORECASE),
        re.compile(r'<embed', re.IGNORECASE),
    ]
    
    @staticmethod
    def check_for_malicious_content(text: str) -> Tuple[bool, List[str]]:
        """
        Check text for potentially malicious content.
        
        Args:
            text: Text to check
            
        Returns:
            Tuple of (is_safe, list_of_issues)
        """
        issues = []
        
        for pattern in SecurityValidator.DANGEROUS_PATTERNS:
            if pattern.search(text):
                issues.append(f"Potentially dangerous pattern detected: {pattern.pattern}")
        
        # Check for SQL injection patterns
        sql_patterns = ['union select', 'drop table', 'delete from', '-- ', '/*']
        for pattern in sql_patterns:
            if pattern.lower() in text.lower():
                issues.append(f"Potential SQL injection pattern: {pattern}")
        
        # Check for path traversal
        if '../' in text or '..\\' in text:
            issues.append("Path traversal pattern detected")
        
        return len(issues) == 0, issues
    
    @staticmethod
    def validate_medical_content(text: str) -> Tuple[bool, List[str]]:
        """
        Validate that content appears to be medical in nature.
        
        Args:
            text: Text to validate
            
        Returns:
            Tuple of (is_medical, list_of_concerns)
        """
        medical_keywords = [
            'patient', 'doctor', 'symptoms', 'diagnosis', 'treatment',
            'medication', 'pain', 'history', 'examination', 'vital signs',
            'blood pressure', 'temperature', 'heart rate', 'breathing',
            'allergies', 'surgery', 'chronic', 'acute', 'prescription'
        ]
        
        concerns = []
        text_lower = text.lower()
        
        # Check for medical keywords
        medical_score = sum(1 for keyword in medical_keywords if keyword in text_lower)
        
        if medical_score == 0 and len(text) > 100:
            concerns.append("No medical keywords detected in substantial text")
        
        # Check for inappropriate content
        inappropriate_keywords = [
            'violent', 'weapon', 'illegal', 'drug dealing', 'suicide'
        ]
        
        for keyword in inappropriate_keywords:
            if keyword in text_lower:
                concerns.append(f"Potentially inappropriate content: {keyword}")
        
        return len(concerns) == 0, concerns


# Validation decorators
def validate_input(validation_func):
    """Decorator to validate function inputs"""
    def decorator(func):
        def wrapper(*args, **kwargs):
            try:
                # Apply validation function to arguments
                validated_args, validated_kwargs = validation_func(*args, **kwargs)
                return func(*validated_args, **validated_kwargs)
            except Exception as e:
                if isinstance(e, (ValidationError, AudioProcessingError)):
                    raise
                else:
                    raise ValidationError(f"Input validation failed: {str(e)}")
        return wrapper
    return decorator


def sanitize_socket_data(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Sanitize socket data for safe processing.
    
    Args:
        data: Socket data dictionary
        
    Returns:
        Sanitized data dictionary
    """
    try:
        return InputValidator.validate_socket_message(data)
    except ValidationError:
        # Return safe fallback for invalid data
        return {'error': 'Invalid data received'} 