import 'package:flutter/material.dart';
import 'package:frontend/screens/splash/splash_screen.dart';
import 'package:frontend/screens/auth/auth_screen.dart';
import 'package:frontend/screens/home/home_screen.dart';
import 'package:frontend/screens/create_revival/create_revival_screen.dart';
import 'package:frontend/screens/character_setup/character_setup_screen.dart';
import 'package:frontend/screens/voice_preview/voice_preview_screen.dart';
import 'package:frontend/screens/conversation/conversation_screen.dart';
import 'package:frontend/screens/history/history_screen.dart';
import 'package:frontend/screens/settings/settings_screen.dart';

class AppRouter {
  static const String splash = '/';
  static const String auth = '/auth';
  static const String home = '/home';
  static const String createRevival = '/create-revival';
  static const String characterSetup = '/character-setup';
  static const String voicePreview = '/voice-preview';
  static const String conversation = '/conversation';
  static const String history = '/history';
  static const String settings = '/settings';

  static Route<dynamic> onGenerateRoute(RouteSettings settings) {
    switch (settings.name) {
      case splash:
        return MaterialPageRoute(builder: (_) => const SplashScreen());
      case auth:
        return MaterialPageRoute(builder: (_) => const AuthScreen());
      case home:
        return MaterialPageRoute(builder: (_) => const HomeScreen());
      case createRevival:
        return MaterialPageRoute(builder: (_) => const CreateRevivalScreen());
      case characterSetup:
        return MaterialPageRoute(builder: (_) => const CharacterSetupScreen());
      case voicePreview:
        return MaterialPageRoute(builder: (_) => const VoicePreviewScreen());
      case conversation:
        return MaterialPageRoute(builder: (_) => const ConversationScreen());
      case history:
        return MaterialPageRoute(builder: (_) => const HistoryScreen());
      case AppRouter.settings:
        return MaterialPageRoute(builder: (_) => const SettingsScreen());
      default:
        return MaterialPageRoute(
          builder: (_) => Scaffold(
            body: Center(child: Text('Route not found: ${settings.name}')),
          ),
        );
    }
  }
}
