import 'dart:async';
import 'package:audioplayers/audioplayers.dart';
import 'package:flutter/foundation.dart';
import 'package:frontend/core/config/app_config.dart';

enum PlayerStatus { idle, loading, playing, paused, completed, error }

class AudioPlayerService {
  final AudioPlayer _player = AudioPlayer();
  PlayerStatus _status = PlayerStatus.idle;
  String? _currentUrl;
  Duration _position = Duration.zero;
  Duration _duration = Duration.zero;

  final StreamController<PlayerStatus> _statusController = StreamController<PlayerStatus>.broadcast();
  final StreamController<Duration> _positionController = StreamController<Duration>.broadcast();
  final StreamController<Duration> _durationController = StreamController<Duration>.broadcast();

  Stream<PlayerStatus> get statusStream => _statusController.stream;
  Stream<Duration> get positionStream => _positionController.stream;
  Stream<Duration> get durationStream => _durationController.stream;

  PlayerStatus get status => _status;
  Duration get position => _position;
  Duration get duration => _duration;
  bool get isPlaying => _status == PlayerStatus.playing;

  AudioPlayerService() {
    _initListeners();
  }

  void _initListeners() {
    _player.onPlayerStateChanged.listen((state) {
      switch (state) {
        case PlayerState.playing:
          _status = PlayerStatus.playing;
          break;
        case PlayerState.paused:
          _status = PlayerStatus.paused;
          break;
        case PlayerState.stopped:
          _status = PlayerStatus.idle;
          break;
        case PlayerState.completed:
          _status = PlayerStatus.completed;
          break;
        default:
          break;
      }
      _statusController.add(_status);
    });

    _player.onPositionChanged.listen((pos) {
      _position = pos;
      _positionController.add(pos);
    });

    _player.onDurationChanged.listen((dur) {
      _duration = dur;
      _durationController.add(dur);
    });

    _player.onPlayerComplete.listen((_) {
      _status = PlayerStatus.completed;
      _position = Duration.zero;
      _statusController.add(_status);
    });
  }

  Future<void> play(String audioUrl) async {
    try {
      _status = PlayerStatus.loading;
      _statusController.add(_status);

      // Prepend host URL if audioUrl is relative (e.g. /storage/generated_audio/...)
      String fullUrl = audioUrl;
      if (audioUrl.startsWith('/')) {
        fullUrl = '${AppConfig.audioHostUrl}$audioUrl';
      }

      _currentUrl = fullUrl;
      await _player.stop();
      await _player.play(UrlSource(fullUrl));
    } catch (e) {
      debugPrint('[AudioPlayer] Playback error: $e');
      _status = PlayerStatus.error;
      _statusController.add(_status);
      throw Exception('Failed to play audio: ${e.toString()}');
    }
  }

  Future<void> pause() async {
    try {
      await _player.pause();
    } catch (_) {}
  }

  Future<void> resume() async {
    try {
      await _player.resume();
    } catch (_) {}
  }

  Future<void> stop() async {
    try {
      await _player.stop();
      _status = PlayerStatus.idle;
      _position = Duration.zero;
      _statusController.add(_status);
    } catch (_) {}
  }

  Future<void> replay() async {
    if (_currentUrl != null) {
      await play(_currentUrl!);
    }
  }

  Future<void> seek(Duration position) async {
    try {
      await _player.seek(position);
    } catch (_) {}
  }

  void dispose() {
    _statusController.close();
    _positionController.close();
    _durationController.close();
    _player.dispose();
  }
}

final audioPlayerService = AudioPlayerService();
