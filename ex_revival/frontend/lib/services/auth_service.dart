import 'package:shared_preferences/shared_preferences.dart';
import 'package:frontend/core/constants/app_constants.dart';
import 'package:frontend/models/user.dart';
import 'package:frontend/services/api_service.dart';

class AuthService {
  String? _token;
  String? _userEmail;
  String? _userId;

  String? get token => _token;
  String? get userEmail => _userEmail;
  String? get userId => _userId;
  bool get isAuthenticated => _token != null && _token!.isNotEmpty;

  Future<void> init() async {
    final prefs = await SharedPreferences.getInstance();
    _token = prefs.getString(AppConstants.tokenKey);
    _userEmail = prefs.getString(AppConstants.userEmailKey);
    _userId = prefs.getString(AppConstants.userIdKey);
    apiService.setAuthToken(_token);
  }

  Future<User> register(String email, String password) async {
    final data = await apiService.post(
      'auth/register',
      body: {'email': email, 'password': password},
    );
    return _saveAuthData(data);
  }

  Future<User> login(String email, String password) async {
    final data = await apiService.post(
      'auth/login',
      body: {'email': email, 'password': password},
    );
    return _saveAuthData(data);
  }

  Future<User> _saveAuthData(dynamic data) async {
    _token = data['access_token'];
    _userEmail = data['email'];
    _userId = data['user_id'];
    apiService.setAuthToken(_token);

    final prefs = await SharedPreferences.getInstance();
    await prefs.setString(AppConstants.tokenKey, _token!);
    await prefs.setString(AppConstants.userEmailKey, _userEmail!);
    await prefs.setString(AppConstants.userIdKey, _userId!);

    return User(
      id: _userId!,
      email: _userEmail!,
      authProvider: 'email',
      createdAt: DateTime.now(),
    );
  }

  Future<void> logout() async {
    _token = null;
    _userEmail = null;
    _userId = null;
    apiService.setAuthToken(null);

    final prefs = await SharedPreferences.getInstance();
    await prefs.remove(AppConstants.tokenKey);
    await prefs.remove(AppConstants.userEmailKey);
    await prefs.remove(AppConstants.userIdKey);
  }
}

final authService = AuthService();
