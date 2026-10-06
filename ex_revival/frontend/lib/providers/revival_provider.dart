import 'package:flutter/foundation.dart';

import 'package:frontend/models/revival.dart';
import 'package:frontend/models/memory.dart';
import 'package:frontend/repositories/revival_repository.dart';
import 'package:frontend/services/audio_player_service.dart';

enum RevivalStatus { initial, loading, loaded, saving, error }

class RevivalProvider extends ChangeNotifier {
  final RevivalRepository _repo;
  RevivalStatus _status = RevivalStatus.initial;
  List<Revival> _revivals = [];
  Revival? _selectedRevival;
  List<Memory> _memories = [];
  String? _errorMessage;

  // Voice preview state
  bool _isPreviewLoading = false;
  VoicePreviewResult? _previewResult;

  RevivalProvider({RevivalRepository? repo}) : _repo = repo ?? revivalRepository;

  RevivalStatus get status => _status;
  List<Revival> get revivals => _revivals;
  Revival? get selectedRevival => _selectedRevival;
  List<Memory> get memories => _memories;
  String? get errorMessage => _errorMessage;
  bool get isPreviewLoading => _isPreviewLoading;
  VoicePreviewResult? get previewResult => _previewResult;

  void selectRevival(Revival revival) {
    _selectedRevival = revival;
    notifyListeners();
    loadMemories(revival.id);
  }

  Future<void> loadRevivals() async {
    _status = RevivalStatus.loading;
    _errorMessage = null;
    notifyListeners();

    try {
      _revivals = await _repo.getRevivals();
      if (_revivals.isNotEmpty && _selectedRevival == null) {
        _selectedRevival = _revivals.first;
        loadMemories(_selectedRevival!.id);
      }
      _status = RevivalStatus.loaded;
      notifyListeners();
    } catch (e) {
      _status = RevivalStatus.error;
      _errorMessage = e.toString();
      notifyListeners();
    }
  }

  Future<Revival?> createRevival({
    required String name,
    String language = 'en',
    String personality = '',
    String speakingStyle = '',
    String relationshipContext = '',
    bool voiceAuthorized = false,
  }) async {
    _status = RevivalStatus.saving;
    _errorMessage = null;
    notifyListeners();

    try {
      final revival = await _repo.createRevival(
        name: name,
        language: language,
        personality: personality,
        speakingStyle: speakingStyle,
        relationshipContext: relationshipContext,
        voiceAuthorized: voiceAuthorized,
      );
      _revivals.insert(0, revival);
      _selectedRevival = revival;
      _status = RevivalStatus.loaded;
      notifyListeners();
      return revival;
    } catch (e) {
      _status = RevivalStatus.error;
      _errorMessage = e.toString();
      notifyListeners();
      return null;
    }
  }

  Future<bool> uploadVoice({
    required String revivalId,
    required Uint8List audioBytes,
    required String filename,
    required bool voiceAuthorized,
  }) async {
    _status = RevivalStatus.saving;
    _errorMessage = null;
    notifyListeners();

    try {
      final updated = await _repo.uploadReferenceVoice(
        id: revivalId,
        audioBytes: audioBytes,
        filename: filename,
        voiceAuthorized: voiceAuthorized,
      );

      final idx = _revivals.indexWhere((r) => r.id == revivalId);
      if (idx != -1) {
        _revivals[idx] = updated;
      }
      if (_selectedRevival?.id == revivalId) {
        _selectedRevival = updated;
      }
      _status = RevivalStatus.loaded;
      notifyListeners();
      return true;
    } catch (e) {
      _status = RevivalStatus.error;
      _errorMessage = e.toString();
      notifyListeners();
      return false;
    }
  }

  Future<VoiceValidationResult?> validateVoice({
    required String revivalId,
    required Uint8List audioBytes,
    required String filename,
  }) async {
    try {
      return await _repo.validateVoice(
        id: revivalId,
        audioBytes: audioBytes,
        filename: filename,
      );
    } catch (e) {
      _errorMessage = e.toString();
      notifyListeners();
      return null;
    }
  }

  Future<bool> previewVoice(String phrase) async {
    if (_selectedRevival == null) return false;
    _isPreviewLoading = true;
    notifyListeners();

    try {
      final res = await _repo.previewVoice(
        id: _selectedRevival!.id,
        phrase: phrase,
      );
      _previewResult = res;
      _isPreviewLoading = false;
      notifyListeners();

      // Automatically play the preview audio
      if (res.audioUrl.isNotEmpty) {
        await audioPlayerService.play(res.audioUrl);
      }
      return true;
    } catch (e) {
      _isPreviewLoading = false;
      _errorMessage = e.toString();
      notifyListeners();
      return false;
    }
  }

  Future<void> updateCharacterConfig({
    required String revivalId,
    String? personality,
    String? speakingStyle,
    String? relationshipContext,
    String? language,
  }) async {
    _status = RevivalStatus.saving;
    notifyListeners();

    try {
      final updated = await _repo.updateRevival(
        revivalId,
        personality: personality,
        speakingStyle: speakingStyle,
        relationshipContext: relationshipContext,
        language: language,
      );
      final idx = _revivals.indexWhere((r) => r.id == revivalId);
      if (idx != -1) _revivals[idx] = updated;
      if (_selectedRevival?.id == revivalId) _selectedRevival = updated;
      _status = RevivalStatus.loaded;
      notifyListeners();
    } catch (e) {
      _status = RevivalStatus.error;
      _errorMessage = e.toString();
      notifyListeners();
    }
  }

  Future<void> deleteRevival(String id) async {
    try {
      await _repo.deleteRevival(id);
      _revivals.removeWhere((r) => r.id == id);
      if (_selectedRevival?.id == id) {
        _selectedRevival = _revivals.isNotEmpty ? _revivals.first : null;
      }
      notifyListeners();
    } catch (e) {
      _errorMessage = e.toString();
      notifyListeners();
    }
  }

  // Memory management
  Future<void> loadMemories(String revivalId) async {
    try {
      _memories = await _repo.getMemories(revivalId);
      notifyListeners();
    } catch (_) {}
  }

  Future<void> addMemory(String revivalId, String text, String importance) async {
    try {
      final mem = await _repo.createMemory(
        revivalId: revivalId,
        memoryText: text,
        importance: importance,
      );
      _memories.insert(0, mem);
      notifyListeners();
    } catch (e) {
      _errorMessage = e.toString();
      notifyListeners();
    }
  }

  Future<void> deleteMemory(String memoryId) async {
    try {
      await _repo.deleteMemory(memoryId);
      _memories.removeWhere((m) => m.id == memoryId);
      notifyListeners();
    } catch (e) {
      _errorMessage = e.toString();
      notifyListeners();
    }
  }

  void clearError() {
    _errorMessage = null;
    notifyListeners();
  }
}
