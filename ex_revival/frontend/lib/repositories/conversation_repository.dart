import 'dart:typed_data';
import 'package:frontend/models/conversation.dart';
import 'package:frontend/services/api_service.dart';

class ConversationRepository {
  final ApiService _api;

  ConversationRepository({ApiService? api}) : _api = api ?? apiService;

  Future<Conversation> createConversation({
    required String revivalId,
    String? title,
  }) async {
    final res = await _api.post(
      'conversations',
      body: {
        'revival_id': revivalId,
        'title': title,
      },
    );
    return Conversation.fromJson(res);
  }

  Future<Conversation> getConversation(String id) async {
    final res = await _api.get('conversations/$id');
    return Conversation.fromJson(res);
  }

  Future<void> deleteConversation(String id) async {
    await _api.delete('conversations/$id');
  }

  Future<ConversationTurnResult> submitTurn({
    required String conversationId,
    Uint8List? audioBytes,
    String? clientTranscript,
  }) async {
    final Map<String, String> fields = {};
    if (clientTranscript != null && clientTranscript.isNotEmpty) {
      fields['client_transcript'] = clientTranscript;
    }

    if (audioBytes != null && audioBytes.isNotEmpty) {
      final res = await _api.multipartPost(
        path: 'conversations/$conversationId/turns',
        fileField: 'audio_file',
        fileBytes: audioBytes,
        filename: 'user_speech.wav',
        fields: fields,
      );
      return ConversationTurnResult.fromJson(res);
    } else {
      // Form submission for text turns matching FastAPI File/Form expectations
      final res = await _api.multipartPost(
        path: 'conversations/$conversationId/turns',
        fields: fields,
      );
      return ConversationTurnResult.fromJson(res);
    }
  }
}

final conversationRepository = ConversationRepository();
