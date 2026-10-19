class VoiceAsset {
  final String id;
  final String revivalId;
  final String storagePath;
  final double durationSeconds;
  final int sampleRate;
  final String status;
  final DateTime createdAt;

  VoiceAsset({
    required this.id,
    required this.revivalId,
    required this.storagePath,
    required this.durationSeconds,
    required this.sampleRate,
    required this.status,
    required this.createdAt,
  });

  factory VoiceAsset.fromJson(Map<String, dynamic> json) {
    return VoiceAsset(
      id: json['id'] ?? '',
      revivalId: json['revival_id'] ?? '',
      storagePath: json['storage_path'] ?? '',
      durationSeconds: (json['duration_seconds'] ?? 0.0).toDouble(),
      sampleRate: json['sample_rate'] ?? 24000,
      status: json['status'] ?? 'valid',
      createdAt: json['created_at'] != null ? DateTime.parse(json['created_at']) : DateTime.now(),
    );
  }
}

class Revival {
  final String id;
  final String userId;
  final String name;
  final String language;
  final String personality;
  final String speakingStyle;
  final String relationshipContext;
  final String? referenceAudioPath;
  final String? personalityDna;
  final bool voiceAuthorized;
  final DateTime createdAt;
  final DateTime updatedAt;
  final List<VoiceAsset> voiceAssets;

  Revival({
    required this.id,
    required this.userId,
    required this.name,
    required this.language,
    required this.personality,
    required this.speakingStyle,
    required this.relationshipContext,
    this.referenceAudioPath,
    this.personalityDna,
    required this.voiceAuthorized,
    required this.createdAt,
    required this.updatedAt,
    this.voiceAssets = const [],
  });

  factory Revival.fromJson(Map<String, dynamic> json) {
    var rawAssets = json['voice_assets'] as List<dynamic>? ?? [];
    List<VoiceAsset> assets = rawAssets.map((a) => VoiceAsset.fromJson(a)).toList();

    return Revival(
      id: json['id'] ?? '',
      userId: json['user_id'] ?? '',
      name: json['name'] ?? '',
      language: json['language'] ?? 'en',
      personality: json['personality'] ?? '',
      speakingStyle: json['speaking_style'] ?? '',
      relationshipContext: json['relationship_context'] ?? '',
      referenceAudioPath: json['reference_audio_path'],
      personalityDna: json['personality_dna'],
      voiceAuthorized: json['voice_authorized'] ?? false,
      createdAt: json['created_at'] != null ? DateTime.parse(json['created_at']) : DateTime.now(),
      updatedAt: json['updated_at'] != null ? DateTime.parse(json['updated_at']) : DateTime.now(),
      voiceAssets: assets,
    );
  }

  bool get hasVoice => referenceAudioPath != null && referenceAudioPath!.isNotEmpty;
}

class VoiceValidationResult {
  final bool isValid;
  final double durationSeconds;
  final int sampleRate;
  final int channels;
  final bool hasSilence;
  final bool hasClipping;
  final String message;

  VoiceValidationResult({
    required this.isValid,
    required this.durationSeconds,
    required this.sampleRate,
    required this.channels,
    required this.hasSilence,
    required this.hasClipping,
    required this.message,
  });

  factory VoiceValidationResult.fromJson(Map<String, dynamic> json) {
    return VoiceValidationResult(
      isValid: json['is_valid'] ?? false,
      durationSeconds: (json['duration_seconds'] ?? 0.0).toDouble(),
      sampleRate: json['sample_rate'] ?? 0,
      channels: json['channels'] ?? 0,
      hasSilence: json['has_silence'] ?? false,
      hasClipping: json['has_clipping'] ?? false,
      message: json['message'] ?? '',
    );
  }
}

class VoicePreviewResult {
  final String audioUrl;
  final String phrase;
  final double durationSeconds;
  final int latencyMs;

  VoicePreviewResult({
    required this.audioUrl,
    required this.phrase,
    required this.durationSeconds,
    required this.latencyMs,
  });

  factory VoicePreviewResult.fromJson(Map<String, dynamic> json) {
    return VoicePreviewResult(
      audioUrl: json['audio_url'] ?? '',
      phrase: json['phrase'] ?? '',
      durationSeconds: (json['duration_seconds'] ?? 0.0).toDouble(),
      latencyMs: json['latency_ms'] ?? 0,
    );
  }
}
