class Memory {
  final String id;
  final String revivalId;
  final String memoryText;
  final String importance; // 'high', 'medium', 'low'
  final DateTime createdAt;

  Memory({
    required this.id,
    required this.revivalId,
    required this.memoryText,
    required this.importance,
    required this.createdAt,
  });

  factory Memory.fromJson(Map<String, dynamic> json) {
    return Memory(
      id: json['id'] ?? '',
      revivalId: json['revival_id'] ?? '',
      memoryText: json['memory_text'] ?? '',
      importance: json['importance'] ?? 'medium',
      createdAt: json['created_at'] != null ? DateTime.parse(json['created_at']) : DateTime.now(),
    );
  }
}
