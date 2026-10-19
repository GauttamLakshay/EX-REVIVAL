import 'dart:async';
import 'dart:io';
import 'package:audioplayers/audioplayers.dart';
import 'package:flutter/foundation.dart';
import 'package:http/http.dart' as http;
import 'package:path_provider/path_provider.dart';
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
  String? get currentUrl => _currentUrl;

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
      try {
        await _player.stop();
      } catch (_) {}

      // On Web: stream directly via UrlSource
      if (kIsWeb) {
        await _player.play(UrlSource(fullUrl));
        return;
      }

      // If already a local file path
      if (!fullUrl.startsWith('http://') && !fullUrl.startsWith('https://')) {
        final localPath = fullUrl.startsWith('file://') ? fullUrl.substring(7) : fullUrl;
        await _player.play(DeviceFileSource(localPath));
        return;
      }

      // For network audio (bypasses Android native MediaPlayer localhost/cleartext issues):
      // Download bytes via Dart HTTP client and play from local application cache.
      try {
        final uri = Uri.parse(fullUrl);
        final rawFilename = uri.pathSegments.isNotEmpty
            ? uri.pathSegments.last
            : 'audio_${fullUrl.hashCode}.wav';
        final cleanFilename = rawFilename.replaceAll(RegExp(r'[^a-zA-Z0-9_\-\.]'), '_');
        final tempDir = await getTemporaryDirectory();
        final cacheFile = File('${tempDir.path}/$cleanFilename');

        if (await cacheFile.exists() && await cacheFile.length() > 0) {
          debugPrint('[AudioPlayer] Playing from local cache: ${cacheFile.path}');
          await _player.play(DeviceFileSource(cacheFile.path));
          return;
        }

        debugPrint('[AudioPlayer] Downloading audio from $fullUrl');
        final response = await http.get(uri).timeout(const Duration(seconds: 15));
        if (response.statusCode == 200 && response.bodyBytes.isNotEmpty) {
          await cacheFile.writeAsBytes(response.bodyBytes);
          debugPrint('[AudioPlayer] Saved ${response.bodyBytes.length} bytes to ${cacheFile.path}');
          await _player.play(DeviceFileSource(cacheFile.path));
          return;
        } else {
          debugPrint('[AudioPlayer] HTTP download status ${response.statusCode}, falling back to UrlSource');
          await _player.play(UrlSource(fullUrl));
          return;
        }
      } catch (cacheErr) {
        debugPrint('[AudioPlayer] Cache strategy failed: $cacheErr, falling back to UrlSource');
        await _player.play(UrlSource(fullUrl));
      }
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
