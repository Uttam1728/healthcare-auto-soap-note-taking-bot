"""
Custom exceptions for the healthcare SOAP note taking bot.
Provides specific exception types for different error scenarios.
"""

from typing import Optional, Dict, Any


class BaseHealthcareException(Exception):
    """Base exception class for all healthcare bot exceptions"""
    
    def __init__(
        self, 
        message: str, 
        error_code: str = None, 
        details: Dict[str, Any] = None,
        cause: Exception = None
    ):
        super().__init__(message)
        self.message = message
        self.error_code = error_code or self.__class__.__name__
        self.details = details or {}
        self.cause = cause
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert exception to dictionary for serialization"""
        result = {
            'error': self.error_code,
            'message': self.message,
            'type': self.__class__.__name__
        }
        
        if self.details:
            result['details'] = self.details
        
        if self.cause:
            result['cause'] = str(self.cause)
        
        return result


# Configuration related exceptions
class ConfigurationError(BaseHealthcareException):
    """Raised when there's a configuration issue"""
    pass


class APIKeyError(ConfigurationError):
    """Raised when API keys are missing or invalid"""
    pass


# Transcription related exceptions
class TranscriptionError(BaseHealthcareException):
    """Base class for transcription-related errors"""
    pass


class DeepgramConnectionError(TranscriptionError):
    """Raised when connection to Deepgram fails"""
    pass


class AudioProcessingError(TranscriptionError):
    """Raised when audio data processing fails"""
    pass


class TranscriptionTimeoutError(TranscriptionError):
    """Raised when transcription times out"""
    pass


# AI Analysis related exceptions
class AnalysisError(BaseHealthcareException):
    """Base class for AI analysis-related errors"""
    pass


class AnthropicAPIError(AnalysisError):
    """Raised when Anthropic API calls fail"""
    pass


class PromptProcessingError(AnalysisError):
    """Raised when prompt processing fails"""
    pass


class JSONParsingError(AnalysisError):
    """Raised when AI response JSON parsing fails"""
    pass


class InsufficientDataError(AnalysisError):
    """Raised when there's insufficient data for analysis"""
    pass


# Data validation exceptions
class ValidationError(BaseHealthcareException):
    """Base class for data validation errors"""
    pass


class TranscriptValidationError(ValidationError):
    """Raised when transcript validation fails"""
    pass


class AnalysisValidationError(ValidationError):
    """Raised when analysis result validation fails"""
    pass


# Socket/Network related exceptions
class SocketError(BaseHealthcareException):
    """Base class for socket-related errors"""
    pass


class ClientConnectionError(SocketError):
    """Raised when client connection issues occur"""
    pass


class DataTransmissionError(SocketError):
    """Raised when data transmission fails"""
    pass


# Service availability exceptions
class ServiceUnavailableError(BaseHealthcareException):
    """Raised when external services are unavailable"""
    pass


class RateLimitError(BaseHealthcareException):
    """Raised when API rate limits are exceeded"""
    pass


# Factory function for creating appropriate exceptions
def create_exception_from_error(
    error: Exception, 
    context: str = None,
    error_code: str = None,
    details: Dict[str, Any] = None
) -> BaseHealthcareException:
    """
    Create appropriate healthcare exception from generic error.
    
    Args:
        error: The original exception
        context: Context where the error occurred
        error_code: Custom error code
        details: Additional error details
        
    Returns:
        Appropriate healthcare exception
    """
    error_message = str(error)
    
    # Determine appropriate exception type based on error characteristics
    if 'api key' in error_message.lower() or 'unauthorized' in error_message.lower():
        return APIKeyError(
            message=f"API authentication failed: {error_message}",
            error_code=error_code,
            details=details,
            cause=error
        )
    
    elif 'deepgram' in error_message.lower() or 'connection' in error_message.lower():
        return DeepgramConnectionError(
            message=f"Deepgram connection error: {error_message}",
            error_code=error_code,
            details=details,
            cause=error
        )
    
    elif 'anthropic' in error_message.lower() or 'claude' in error_message.lower():
        return AnthropicAPIError(
            message=f"Anthropic API error: {error_message}",
            error_code=error_code,
            details=details,
            cause=error
        )
    
    elif 'json' in error_message.lower() or 'parse' in error_message.lower():
        return JSONParsingError(
            message=f"JSON parsing error: {error_message}",
            error_code=error_code,
            details=details,
            cause=error
        )
    
    elif 'timeout' in error_message.lower():
        return TranscriptionTimeoutError(
            message=f"Operation timeout: {error_message}",
            error_code=error_code,
            details=details,
            cause=error
        )
    
    else:
        # Generic healthcare exception for unclassified errors
        return BaseHealthcareException(
            message=f"Healthcare bot error in {context or 'unknown context'}: {error_message}",
            error_code=error_code or 'UNKNOWN_ERROR',
            details=details,
            cause=error
        )


class ErrorHandler:
    """Centralized error handling utilities"""
    
    @staticmethod
    def handle_api_error(error: Exception, api_name: str) -> BaseHealthcareException:
        """Handle API-related errors with context"""
        return create_exception_from_error(
            error,
            context=f"{api_name} API",
            details={'api': api_name}
        )
    
    @staticmethod
    def handle_service_error(error: Exception, service_name: str) -> BaseHealthcareException:
        """Handle service-related errors with context"""
        return create_exception_from_error(
            error,
            context=f"{service_name} service",
            details={'service': service_name}
        )
    
    @staticmethod
    def validate_required_field(value: Any, field_name: str) -> None:
        """Validate that a required field is present and not empty"""
        if value is None or (isinstance(value, str) and not value.strip()):
            raise ValidationError(
                message=f"Required field '{field_name}' is missing or empty",
                error_code="MISSING_REQUIRED_FIELD",
                details={'field_name': field_name}
            )
    
    @staticmethod
    def validate_transcript_length(transcript: str, min_length: int = 10) -> None:
        """Validate transcript has minimum required length"""
        if not transcript or len(transcript.strip()) < min_length:
            raise InsufficientDataError(
                message=f"Transcript too short for analysis (minimum {min_length} characters required)",
                error_code="INSUFFICIENT_TRANSCRIPT_DATA",
                details={
                    'transcript_length': len(transcript) if transcript else 0,
                    'minimum_required': min_length
                }
            ) 