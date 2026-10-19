import 'dart:async';
import 'dart:io';
import 'package:flutter/foundation.dart';
import 'package:record/record.dart';
import 'package:path_provider/path_provider.dart';

enum RecordingState { idle, recording, stopped, error }

class AudioRecorderService {
  final AudioRecorder _recorder = AudioRecorder();
  RecordingState _state = RecordingState.idle;
  Timer? _durationTimer;
  int _recordDurationSeconds = 0;


  final StreamController<int> _durationController = StreamController<int>.broadcast();
  final StreamController<double> _amplitudeController = StreamController<double>.broadcast();

  Stream<int> get durationStream => _durationController.stream;
  Stream<double> get amplitudeStream => _amplitudeController.stream;
  RecordingState get state => _state;
  int get durationSeconds => _recordDurationSeconds;

  Future<bool> hasPermission() async {
    try {
      return await _recorder.hasPermission();
    } catch (e) {
      debugPrint('[AudioRecorder] Permission check error: $e');
      return false;
    }
  }

  Future<void> startRecording() async {
    final permitted = await hasPermission();
    if (!permitted) {
      _state = RecordingState.error;
      throw Exception('Microphone permission was denied.');
    }

    try {
      _recordDurationSeconds = 0;
      _durationController.add(0);

      String filePath = '';
      if (!kIsWeb) {
        final tempDir = await getTemporaryDirectory();
        filePath = '${tempDir.path}/rec_${DateTime.now().millisecondsSinceEpoch}.wav';
      }


      await _recorder.start(
        const RecordConfig(
          encoder: AudioEncoder.wav,
          sampleRate: 16000,
          numChannels: 1,
        ),
        path: filePath,
      );

      _state = RecordingState.recording;

      _durationTimer = Timer.periodic(const Duration(seconds: 1), (timer) {
        _recordDurationSeconds++;
        _durationController.add(_recordDurationSeconds);
      });

      // Periodic amplitude polling for audio waveform animation
      _startAmplitudeMonitoring();
    } catch (e) {
      _state = RecordingState.error;
      _durationTimer?.cancel();
      throw Exception('Failed to start recording: ${e.toString()}');
    }
  }

  void _startAmplitudeMonitoring() {
    Timer.periodic(const Duration(milliseconds: 100), (timer) async {
      if (_state != RecordingState.recording) {
        timer.cancel();
        return;
      }
      try {
        final amp = await _recorder.getAmplitude();
        // Normalize dB (-60 to 0) to 0.0 -> 1.0
        double normalized = (amp.current + 60) / 60;
        if (normalized < 0) normalized = 0;
        if (normalized > 1) normalized = 1;
        _amplitudeController.add(normalized);
      } catch (_) {}
    });
  }

  Future<Uint8List?> stopRecording() async {
    _durationTimer?.cancel();
    if (_state != RecordingState.recording) return null;

    try {
      final path = await _recorder.stop();
      _state = RecordingState.stopped;

      if (path != null && !kIsWeb) {
        final file = File(path);
        if (await file.exists()) {
          final bytes = await file.readAsBytes();
          if (bytes.length < 8000) {
            throw Exception('Recording was too short. Hold the microphone while speaking.');
          }
          return bytes;
        }
      }
      return null;
    } catch (e) {
      _state = RecordingState.error;
      throw Exception('Failed to finalize audio recording: ${e.toString()}');
    }
  }

  Future<void> cancel() async {
    _durationTimer?.cancel();
    try {
      await _recorder.cancel();
    } catch (_) {}
    _state = RecordingState.idle;
  }

  void dispose() {
    _durationTimer?.cancel();
    _durationController.close();
    _amplitudeController.close();
    _recorder.dispose();
  }
}

final audioRecorderService = AudioRecorderService();
