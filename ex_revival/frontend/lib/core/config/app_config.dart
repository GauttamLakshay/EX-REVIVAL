import 'package:flutter/foundation.dart';

class AppConfig {
  static const String appName = 'EX REVIVAL';
  static const String appTagline = 'Voice-First AI Presence';
  static const String version = '1.0.0';

  // Configurable base URL: can be overridden via --dart-define=API_HOST=...
  static const String _customHost = String.fromEnvironment('API_HOST', defaultValue: '');

  static String get host {
    if (_customHost.isNotEmpty) {
      return _customHost;
    }
    if (kIsWeb) {
      return 'http://localhost:8000';
    }
    // Default to 127.0.0.1:8000 which works seamlessly over USB via `adb reverse tcp:8000 tcp:8000`
    // (bypassing router AP isolation / cellular data mismatch), and on desktop / iOS simulators.
    return 'http://127.0.0.1:8000';
  }

  // Configurable base URL
  static String get apiBaseUrl => '$host/api/v1';

  // Audio host base URL for static file storage (/storage)
  static String get audioHostUrl => host;

  // Extended timeout to accommodate CPU neural synthesis latency
  static const Duration requestTimeout = Duration(seconds: 300);
}
