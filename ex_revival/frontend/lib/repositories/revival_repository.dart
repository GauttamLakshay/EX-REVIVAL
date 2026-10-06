import 'dart:typed_data';
import 'package:frontend/models/revival.dart';
import 'package:frontend/models/memory.dart';
import 'package:frontend/services/api_service.dart';

class RevivalRepository {
  final ApiService _api;

  RevivalRepository({ApiService? api}) : _api = api ?? apiService;

  Future<Revival> createRevival({
    required String name,
    String language = 'en',
    String personality = '',
    String speakingStyle = '',
    String relationshipContext = '',
    bool voiceAuthorized = false,
  }) async {
    final res = await _api.post(
      'revivals',
      body: {
        'name': name,
        'language': language,
        'personality': personality,
        'speaking_style': speakingStyle,
        'relationship_context': relationshipContext,
        'voice_authorized': voiceAuthorized,
      },
    );
    return Revival.fromJson(res);
  }

  Future<List<Revival>> getRevivals() async {
    final res = await _api.get('revivals') as List<dynamic>;
    return res.map((item) => Revival.fromJson(item)).toList();
  }

  Future<Revival> getRevival(String id) async {
    final res = await _api.get('revivals/$id');
    return Revival.fromJson(res);
  }

  Future<Revival> updateRevival(
    String id, {
    String? name,
    String? language,
    String? personality,
    String? speakingStyle,
    String? relationshipContext,
    bool? voiceAuthorized,
  }) async {
    final Map<String, dynamic> body = {};
    if (name != null) body['name'] = name;
    if (language != null) body['language'] = language;
    if (personality != null) body['personality'] = personality;
    if (speakingStyle != null) body['speaking_style'] = speakingStyle;
    if (relationshipContext != null) body['relationship_context'] = relationshipContext;
    if (voiceAuthorized != null) body['voice_authorized'] = voiceAuthorized;

    final res = await _api.patch('revivals/$id', body: body);
    return Revival.fromJson(res);
  }

  Future<void> deleteRevival(String id) async {
    await _api.delete('revivals/$id');
  }

  Future<Revival> uploadReferenceVoice({
    required String id,
    required Uint8List audioBytes,
    required String filename,
    required bool voiceAuthorized,
  }) async {
    final res = await _api.multipartPost(
      path: 'revivals/$id/voice',
      fileField: 'audio_file',
      fileBytes: audioBytes,
      filename: filename,
      fields: {'voice_authorized': voiceAuthorized.toString()},
    );
    return Revival.fromJson(res);
  }

  Future<VoiceValidationResult> validateVoice({
    required String id,
    required Uint8List audioBytes,
    required String filename,
  }) async {
    final res = await _api.multipartPost(
      path: 'revivals/$id/voice/validate',
      fileField: 'audio_file',
      fileBytes: audioBytes,
      filename: filename,
    );
    return VoiceValidationResult.fromJson(res);
  }

  Future<VoicePreviewResult> previewVoice({
    required String id,
    required String phrase,
  }) async {
    final res = await _api.post(
      'revivals/$id/voice/preview',
      body: {'phrase': phrase},
    );
    return VoicePreviewResult.fromJson(res);
  }

  Future<List<Memory>> getMemories(String revivalId) async {
    final res = await _api.get('revivals/$revivalId/memories') as List<dynamic>;
    return res.map((item) => Memory.fromJson(item)).toList();
  }

  Future<Memory> createMemory({
    required String revivalId,
    required String memoryText,
    String importance = 'medium',
  }) async {
    final res = await _api.post(
      'revivals/$revivalId/memories',
      body: {
        'memory_text': memoryText,
        'importance': importance,
      },
    );
    return Memory.fromJson(res);
  }

  Future<void> deleteMemory(String memoryId) async {
    await _api.delete('memories/$memoryId');
  }
}

final revivalRepository = RevivalRepository();
