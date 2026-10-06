class AppError implements Exception {
  final String message;
  final String? code;
  final dynamic details;

  AppError(this.message, {this.code, this.details});

  @override
  String toString() => message;
}

class NetworkError extends AppError {
  NetworkError([String? message])
      : super(message ?? 'Connection lost. Check your internet connection.', code: 'NETWORK_ERROR');
}

class STTError extends AppError {
  STTError([String? message])
      : super(message ?? "I couldn't understand that. Try speaking again.", code: 'STT_ERROR');
}

class LLMError extends AppError {
  LLMError([String? message])
      : super(message ?? 'AI response generation failed. Please try again.', code: 'LLM_ERROR');
}

class VoiceSynthesisError extends AppError {
  VoiceSynthesisError([String? message])
      : super(message ?? 'Voice synthesis failed. You can still view the text response.', code: 'VOICE_ERROR');
}

class AuthError extends AppError {
  AuthError([String? message])
      : super(message ?? 'Authentication failed. Please check your credentials.', code: 'AUTH_ERROR');
}
