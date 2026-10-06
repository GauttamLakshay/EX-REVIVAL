class User {
  final String id;
  final String email;
  final String authProvider;
  final DateTime createdAt;

  User({
    required this.id,
    required this.email,
    required this.authProvider,
    required this.createdAt,
  });

  factory User.fromJson(Map<String, dynamic> json) {
    return User(
      id: json['id'] ?? '',
      email: json['email'] ?? '',
      authProvider: json['auth_provider'] ?? 'email',
      createdAt: json['created_at'] != null ? DateTime.parse(json['created_at']) : DateTime.now(),
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'id': id,
      'email': email,
      'auth_provider': authProvider,
      'created_at': createdAt.toIso8601String(),
    };
  }
}
