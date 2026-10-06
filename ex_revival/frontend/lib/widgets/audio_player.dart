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

  @override
  void initState() {
    super.initState();
    audioPlayerService.statusStream.listen((status) {
      if (mounted) {
        setState(() {
          _isPlaying = status == PlayerStatus.playing;
        });
      }
    });

    audioPlayerService.positionStream.listen((pos) {
      if (mounted) setState(() => _position = pos);
    });

    audioPlayerService.durationStream.listen((dur) {
      if (mounted) setState(() => _duration = dur);
    });
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
