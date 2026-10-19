import 'dart:convert';
import 'dart:typed_data';
import 'package:http/http.dart' as http;
import 'package:http_parser/http_parser.dart';
import 'package:frontend/core/config/app_config.dart';
import 'package:frontend/core/errors/app_error.dart';

class ApiService {
  String? _authToken;

  void setAuthToken(String? token) {
    _authToken = token;
  }

  Map<String, String> _headers({bool isJson = true}) {
    final headers = <String, String>{};
    if (isJson) {
      headers['Content-Type'] = 'application/json';
    }
    if (_authToken != null && _authToken!.isNotEmpty) {
      headers['Authorization'] = 'Bearer $_authToken';
    }
    return headers;
  }

  Uri _uri(String path) {
    final cleanPath = path.startsWith('/') ? path.substring(1) : path;
    return Uri.parse('${AppConfig.apiBaseUrl}/$cleanPath');
  }

  Future<dynamic> get(String path) async {
    try {
      final response = await http
          .get(_uri(path), headers: _headers())
          .timeout(AppConfig.requestTimeout);
      return _processResponse(response);
    } catch (e) {
      if (e is AppError) rethrow;
      throw NetworkError('Network request failed: ${e.toString()}');
    }
  }

  Future<dynamic> post(String path, {dynamic body}) async {
    try {
      final response = await http
          .post(
            _uri(path),
            headers: _headers(),
            body: body != null ? jsonEncode(body) : null,
          )
          .timeout(AppConfig.requestTimeout);
      return _processResponse(response);
    } catch (e) {
      if (e is AppError) rethrow;
      throw NetworkError('Network request failed: ${e.toString()}');
    }
  }

  Future<dynamic> patch(String path, {dynamic body}) async {
    try {
      final response = await http
          .patch(
            _uri(path),
            headers: _headers(),
            body: body != null ? jsonEncode(body) : null,
          )
          .timeout(AppConfig.requestTimeout);
      return _processResponse(response);
    } catch (e) {
      if (e is AppError) rethrow;
      throw NetworkError('Network request failed: ${e.toString()}');
    }
  }

  Future<dynamic> delete(String path) async {
    try {
      final response = await http
          .delete(_uri(path), headers: _headers())
          .timeout(AppConfig.requestTimeout);
      return _processResponse(response);
    } catch (e) {
      if (e is AppError) rethrow;
      throw NetworkError('Network request failed: ${e.toString()}');
    }
  }

  Future<dynamic> multipartPost({
    required String path,
    String? fileField,
    Uint8List? fileBytes,
    String? filename,
    Map<String, String>? fields,
  }) async {
    try {
      final request = http.MultipartRequest('POST', _uri(path));
      if (_authToken != null) {
        request.headers['Authorization'] = 'Bearer $_authToken';
      }

      if (fields != null) {
        request.fields.addAll(fields);
      }

      if (fileBytes != null && fileField != null) {
        MediaType mediaType;
        final fn = (filename ?? '').toLowerCase();
        if (fn.endsWith('.mp3')) {
          mediaType = MediaType('audio', 'mpeg');
        } else if (fn.endsWith('.ogg') || fn.endsWith('.oga') || fn.endsWith('.opus')) {
          mediaType = MediaType('audio', 'ogg');
        } else if (fn.endsWith('.m4a') || fn.endsWith('.aac') || fn.endsWith('.mp4')) {
          mediaType = MediaType('audio', 'mp4');
        } else {
          mediaType = MediaType('audio', 'wav');
        }

        request.files.add(
          http.MultipartFile.fromBytes(
            fileField,
            fileBytes,
            filename: filename ?? 'audio.wav',
            contentType: mediaType,
          ),
        );
      }

      final streamedResponse = await request.send().timeout(AppConfig.requestTimeout);
      final response = await http.Response.fromStream(streamedResponse);
      return _processResponse(response);
    } catch (e) {
      if (e is AppError) rethrow;
      throw NetworkError('Failed to send request: ${e.toString()}');
    }
  }

  dynamic _processResponse(http.Response response) {
    if (response.statusCode >= 200 && response.statusCode < 300) {
      if (response.body.isEmpty) return null;
      return jsonDecode(response.body);
    }

    String errorMessage = 'Request failed (${response.statusCode})';
    try {
      final body = jsonDecode(response.body);
      if (body is Map && body.containsKey('detail')) {
        errorMessage = body['detail'].toString();
      }
    } catch (_) {}

    if (response.statusCode == 401) {
      throw AuthError(errorMessage);
    }
    throw AppError(errorMessage, code: 'HTTP_${response.statusCode}');
  }
}

final apiService = ApiService();
