import 'dart:async';
import 'package:flutter/foundation.dart';

import 'package:frontend/models/conversation.dart';
import 'package:frontend/models/message.dart';
import 'package:frontend/repositories/conversation_repository.dart';
import 'package:frontend/services/audio_recorder_service.dart';
import 'package:frontend/services/audio_player_service.dart';

enum ConversationState {
  idle,
  listening,
  uploading,
  transcribing,
  thinking,
  generatingVoice,
  speaking,
  error,
}

class ConversationProvider extends ChangeNotifier {
  final ConversationRepository _repo;
  ConversationState _state = ConversationState.idle;
  Conversation? _currentConversation;
  List<Message> _messages = [];
  String? _errorMessage;
  int _recordingDuration = 0;
  double _currentAmplitude = 0.0;

  StreamSubscription? _durationSub;
  StreamSubscription? _ampSub;
  StreamSubscription? _playerSub;

  ConversationProvider({ConversationRepository? repo}) : _repo = repo ?? conversationRepository {
    _initAudioListeners();
  }

  ConversationState get state => _state;
  Conversation? get currentConversation => _currentConversation;
  List<Message> get messages => _messages;
  String? get errorMessage => _errorMessage;
  int get recordingDuration => _recordingDuration;
  double get currentAmplitude => _currentAmplitude;
  bool get isRecording => _state == ConversationState.listening;
  bool get isSpeaking => _state == ConversationState.speaking;
  bool get isProcessing =>
      _state == ConversationState.uploading ||
      _state == ConversationState.transcribing ||
      _state == ConversationState.thinking ||
      _state == ConversationState.generatingVoice;

  void _initAudioListeners() {
    _durationSub = audioRecorderService.durationStream.listen((sec) {
      _recordingDuration = sec;
      notifyListeners();
    });

    _ampSub = audioRecorderService.amplitudeStream.listen((amp) {
      _currentAmplitude = amp;
      notifyListeners();
    });

    _playerSub = audioPlayerService.statusStream.listen((playerStatus) {
      if (playerStatus == PlayerStatus.playing) {
        _state = ConversationState.speaking;
        notifyListeners();
      } else if (playerStatus == PlayerStatus.completed || playerStatus == PlayerStatus.idle) {
        if (_state == ConversationState.speaking) {
          _state = ConversationState.idle;
          notifyListeners();
        }
      }
    });
  }

  Future<void> startNewConversation(String revivalId, {String? title}) async {
    _state = ConversationState.idle;
    _errorMessage = null;
    notifyListeners();

    try {
      final conv = await _repo.createConversation(revivalId: revivalId, title: title);
      _currentConversation = conv;
      _messages = [];
      notifyListeners();
    } catch (e) {
      _state = ConversationState.error;
      _errorMessage = e.toString();
      notifyListeners();
    }
  }

  Future<void> loadConversation(String conversationId) async {
    _state = ConversationState.idle;
    _errorMessage = null;
    notifyListeners();

    try {
      final conv = await _repo.getConversation(conversationId);
      _currentConversation = conv;
      _messages = List.from(conv.messages);
      notifyListeners();
    } catch (e) {
      _state = ConversationState.error;
      _errorMessage = e.toString();
      notifyListeners();
    }
  }

  Future<void> startRecording() async {
    if (_state == ConversationState.speaking) {
      await audioPlayerService.stop();
    }

    try {
      _errorMessage = null;
      await audioRecorderService.startRecording();
      _state = ConversationState.listening;
      notifyListeners();
    } catch (e) {
      _state = ConversationState.error;
      _errorMessage = e.toString();
      notifyListeners();
    }
  }

  Future<void> stopAndSubmitRecording() async {
    if (_state != ConversationState.listening) return;

    try {
      _state = ConversationState.uploading;
      notifyListeners();

      final audioBytes = await audioRecorderService.stopRecording();
      if (audioBytes == null || audioBytes.isEmpty) {
        _state = ConversationState.idle;
        notifyListeners();
        return;
      }

      await submitTurn(audioBytes: audioBytes);
    } catch (e) {
      _state = ConversationState.error;
      _errorMessage = e.toString();
      notifyListeners();
    }
  }

  Future<void> cancelRecording() async {
    await audioRecorderService.cancel();
    _state = ConversationState.idle;
    notifyListeners();
  }

  Future<void> submitTurn({Uint8List? audioBytes, String? clientTranscript}) async {
    if (_currentConversation == null) return;

    try {
      _state = ConversationState.thinking;
      notifyListeners();

      final result = await _repo.submitTurn(
        conversationId: _currentConversation!.id,
        audioBytes: audioBytes,
        clientTranscript: clientTranscript,
      );

      // Add user message
      _messages.add(
        Message(
          id: 'user_${DateTime.now().millisecondsSinceEpoch}',
          conversationId: _currentConversation!.id,
          role: 'user',
          text: result.transcript,
          createdAt: DateTime.now(),
        ),
      );

      // Add assistant message
      final assistantMsg = Message(
        id: result.turnId,
        conversationId: _currentConversation!.id,
        role: 'assistant',
        text: result.responseText,
        audioUrl: result.audioUrl,
        latencyMs: result.latencyMs,
        createdAt: DateTime.now(),
      );
      _messages.add(assistantMsg);

      notifyListeners();

      // Automatically play generated audio
      if (result.audioUrl.isNotEmpty) {
        _state = ConversationState.speaking;
        notifyListeners();
        await audioPlayerService.play(result.audioUrl);
      } else {
        _state = ConversationState.idle;
        notifyListeners();
      }
    } catch (e) {
      _state = ConversationState.error;
      _errorMessage = e.toString();
      notifyListeners();
    }
  }

  Future<void> playMessageAudio(Message message) async {
    if (message.audioUrl != null && message.audioUrl!.isNotEmpty) {
      await audioPlayerService.play(message.audioUrl!);
    }
  }

  Future<void> stopPlayback() async {
    await audioPlayerService.stop();
    _state = ConversationState.idle;
    notifyListeners();
  }

  void clearError() {
    _errorMessage = null;
    _state = ConversationState.idle;
    notifyListeners();
  }

  @override
  void dispose() {
    _durationSub?.cancel();
    _ampSub?.cancel();
    _playerSub?.cancel();
    super.dispose();
  }
}
