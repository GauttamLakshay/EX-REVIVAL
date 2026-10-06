import 'package:frontend/models/user.dart';
import 'package:frontend/services/auth_service.dart';

class AuthRepository {
  final AuthService _authService;

  AuthRepository({AuthService? service}) : _authService = service ?? authService;

  bool get isAuthenticated => _authService.isAuthenticated;

  String? get currentEmail => _authService.userEmail;
  String? get currentUserId => _authService.userId;

  Future<User> login(String email, String password) => _authService.login(email, password);
  Future<User> register(String email, String password) => _authService.register(email, password);
  Future<void> logout() => _authService.logout();
}

final authRepository = AuthRepository();
