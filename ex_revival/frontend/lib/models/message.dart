class Message {
  final String id;
  final String conversationId;
  final String role; // 'user' or 'assistant'
  final String text;
  final String? audioPath;
  final String? audioUrl;
  final int? latencyMs;
  final DateTime createdAt;

  Message({
    required this.id,
    required this.conversationId,
    required this.role,
    required this.text,
    this.audioPath,
    this.audioUrl,
    this.latencyMs,
    required this.createdAt,
  });

  bool get isUser => role == 'user';
  bool get hasAudio => audioUrl != null && audioUrl!.isNotEmpty;

  factory Message.fromJson(Map<String, dynamic> json) {
    return Message(
      id: json['id'] ?? '',
      conversationId: json['conversation_id'] ?? '',
      role: json['role'] ?? 'user',
      text: json['text'] ?? '',
      audioPath: json['audio_path'],
      audioUrl: json['audio_url'],
      latencyMs: json['latency_ms'],
      createdAt: json['created_at'] != null ? DateTime.parse(json['created_at']) : DateTime.now(),
    );
  }
}
