import 'package:flutter/foundation.dart';

class AppConfig {
  static const String appName = 'EX REVIVAL';
  static const String appTagline = 'Voice-First AI Presence';
  static const String version = '1.0.0';

  // Configurable base URL
  static String get apiBaseUrl {
    if (kIsWeb) {
      return 'http://localhost:8000/api/v1';
    }
    // On physical mobile device or desktop
    return 'http://localhost:8000/api/v1';
  }

  // Audio host base URL for static file storage (/storage)
  static String get audioHostUrl {
    return 'http://localhost:8000';
  }

  static const Duration requestTimeout = Duration(seconds: 45);
}
