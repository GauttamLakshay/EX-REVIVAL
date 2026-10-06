import 'package:frontend/models/message.dart';

class Conversation {
  final String id;
  final String revivalId;
  final String title;
  final DateTime startedAt;
  final DateTime? endedAt;
  final List<Message> messages;

  Conversation({
    required this.id,
    required this.revivalId,
    required this.title,
    required this.startedAt,
    this.endedAt,
    this.messages = const [],
  });

  factory Conversation.fromJson(Map<String, dynamic> json) {
    var rawMsgs = json['messages'] as List<dynamic>? ?? [];
    List<Message> msgs = rawMsgs.map((m) => Message.fromJson(m)).toList();

    return Conversation(
      id: json['id'] ?? '',
      revivalId: json['revival_id'] ?? '',
      title: json['title'] ?? 'Conversation',
      startedAt: json['started_at'] != null ? DateTime.parse(json['started_at']) : DateTime.now(),
      endedAt: json['ended_at'] != null ? DateTime.parse(json['ended_at']) : null,
      messages: msgs,
    );
  }
}

class ConversationTurnResult {
  final String turnId;
  final String conversationId;
  final String transcript;
  final String responseText;
  final String audioUrl;
  final int latencyMs;
  final int sttLatencyMs;
  final int llmLatencyMs;
  final int voiceLatencyMs;
  final String status;

  ConversationTurnResult({
    required this.turnId,
    required this.conversationId,
    required this.transcript,
    required this.responseText,
    required this.audioUrl,
    required this.latencyMs,
    required this.sttLatencyMs,
    required this.llmLatencyMs,
    required this.voiceLatencyMs,
    required this.status,
  });

  factory ConversationTurnResult.fromJson(Map<String, dynamic> json) {
    return ConversationTurnResult(
      turnId: json['turn_id'] ?? '',
      conversationId: json['conversation_id'] ?? '',
      transcript: json['transcript'] ?? '',
      responseText: json['response_text'] ?? '',
      audioUrl: json['audio_url'] ?? '',
      latencyMs: json['latency_ms'] ?? 0,
      sttLatencyMs: json['stt_latency_ms'] ?? 0,
      llmLatencyMs: json['llm_latency_ms'] ?? 0,
      voiceLatencyMs: json['voice_latency_ms'] ?? 0,
      status: json['status'] ?? 'completed',
    );
  }
}
