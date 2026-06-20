// lib/core/constants/app_constants.dart
class AppConstants {
  // Backend base URL — swap for production
  static const String baseUrl       = 'http://10.0.2.2:5000'; // Android emulator
  static const String wsUrl         = 'ws://10.0.2.2:5000';   // WebSocket
  static const String chatEndpoint  = '/chat';
  static const String chatStreamEndpoint = '/chat/stream';
  static const String wsEndpoint    = '/ws/chat';
  static const String predictEndpoint = '/predict';
  static const String scanEndpoint  = '/scan';
  static const String historyEndpoint = '/history';
  static const String healthEndpoint = '/health';

  // Timeouts
  static const int connectTimeout   = 10000; // ms
  static const int receiveTimeout   = 60000; // ms

  // Keys
  static const String authTokenKey  = 'auth_token';
  static const String userKey       = 'user_data';
  static const String chatHistoryKey = 'chat_history';

  // UI
  static const double borderRadius  = 16.0;
  static const double cardRadius    = 16.0;
  static const double inputRadius   = 14.0;
  static const double horizontalPad = 20.0;
}

class AppStrings {
  static const String appName       = 'MedAI';
  static const String appTagline    = 'Your AI health companion';
  static const String chatTitle     = 'AI Doctor';
  static const String diagnosisTitle = 'Disease Prediction';
  static const String scanTitle     = 'Medical Scan';
  static const String historyTitle  = 'Health History';
  static const String profileTitle  = 'Profile';
  static const String chatHint      = 'Describe your symptoms...';
  static const String disclaimer    =
      'MedAI is an AI assistant and does not replace professional medical advice. '
      'Always consult a qualified healthcare provider for medical decisions.';
}
