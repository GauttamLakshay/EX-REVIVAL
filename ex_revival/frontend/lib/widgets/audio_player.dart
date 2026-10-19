import 'dart:async';
import 'package:flutter/material.dart';
import 'package:frontend/core/theme/app_theme.dart';
import 'package:frontend/services/audio_player_service.dart';

class AudioPlayerBarWidget extends StatefulWidget {
  final String audioUrl;
  final String title;

  const AudioPlayerBarWidget({
    super.key,
    required this.audioUrl,
    required this.title,
  });

  @override
  State<AudioPlayerBarWidget> createState() => _AudioPlayerBarWidgetState();
}

class _AudioPlayerBarWidgetState extends State<AudioPlayerBarWidget> {
  bool _isPlaying = false;
  Duration _position = Duration.zero;
  Duration _duration = Duration.zero;

  StreamSubscription<PlayerStatus>? _statusSub;
  StreamSubscription<Duration>? _positionSub;
  StreamSubscription<Duration>? _durationSub;

  @override
  void initState() {
    super.initState();
    _statusSub = audioPlayerService.statusStream.listen((status) {
      if (mounted) {
        final current = audioPlayerService.currentUrl;
        final isThisPlaying = status == PlayerStatus.playing &&
            current != null &&
            (current == widget.audioUrl || current.endsWith(widget.audioUrl));
        setState(() {
          _isPlaying = isThisPlaying;
          if (!isThisPlaying && status == PlayerStatus.idle) {
            _position = Duration.zero;
          }
        });
      }
    });

    _positionSub = audioPlayerService.positionStream.listen((pos) {
      if (mounted && _isPlaying) setState(() => _position = pos);
    });

    _durationSub = audioPlayerService.durationStream.listen((dur) {
      if (mounted && _isPlaying) setState(() => _duration = dur);
    });
  }

  @override
  void dispose() {
    _statusSub?.cancel();
    _positionSub?.cancel();
    _durationSub?.cancel();
    super.dispose();
  }

  void _togglePlay() {
    if (_isPlaying) {
      audioPlayerService.pause();
    } else {
      audioPlayerService.play(widget.audioUrl);
    }
  }

  @override
  Widget build(BuildContext context) {
    final posText = '${_position.inSeconds}s';
    final durText = _duration.inSeconds > 0 ? '${_duration.inSeconds}s' : '--';

    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
      decoration: BoxDecoration(
        color: AppTheme.surfaceElevated,
        borderRadius: BorderRadius.circular(16),
        border: Border.all(color: const Color(0xFF2B2F44)),
      ),
      child: Row(
        children: [
          IconButton(
            onPressed: _togglePlay,
            icon: Icon(
              _isPlaying ? Icons.pause_circle_filled_rounded : Icons.play_circle_fill_rounded,
              color: AppTheme.accent,
              size: 36,
            ),
          ),
          const SizedBox(width: 8),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              mainAxisSize: MainAxisSize.min,
              children: [
                Text(
                  widget.title,
                  style: const TextStyle(
                    color: AppTheme.textPrimary,
                    fontSize: 13,
                    fontWeight: FontWeight.w600,
                  ),
                  maxLines: 1,
                  overflow: TextOverflow.ellipsis,
                ),
                const SizedBox(height: 4),
                ClipRRect(
                  borderRadius: BorderRadius.circular(4),
                  child: LinearProgressIndicator(
                    value: _duration.inMilliseconds > 0
                        ? (_position.inMilliseconds / _duration.inMilliseconds).clamp(0.0, 1.0)
                        : 0.0,
                    backgroundColor: const Color(0xFF262A3C),
                    valueColor: const AlwaysStoppedAnimation<Color>(AppTheme.accent),
                    minHeight: 4,
                  ),
                ),
              ],
            ),
          ),
          const SizedBox(width: 12),
          Text(
            '$posText / $durText',
            style: const TextStyle(color: AppTheme.textMuted, fontSize: 11),
          ),
        ],
      ),
    );
  }
}
