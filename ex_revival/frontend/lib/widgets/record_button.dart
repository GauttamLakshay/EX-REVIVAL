import 'package:flutter/material.dart';
import 'package:frontend/core/theme/app_theme.dart';

class RecordButtonWidget extends StatefulWidget {
  final bool isRecording;
  final bool isProcessing;
  final VoidCallback onStart;
  final VoidCallback onStop;
  final int durationSeconds;

  const RecordButtonWidget({
    super.key,
    required this.isRecording,
    required this.isProcessing,
    required this.onStart,
    required this.onStop,
    this.durationSeconds = 0,
  });

  @override
  State<RecordButtonWidget> createState() => _RecordButtonWidgetState();
}

class _RecordButtonWidgetState extends State<RecordButtonWidget> with SingleTickerProviderStateMixin {
  late AnimationController _pulseController;
  late Animation<double> _scaleAnimation;

  @override
  void initState() {
    super.initState();
    _pulseController = AnimationController(
      vsync: this,
      duration: const Duration(milliseconds: 1000),
    )..repeat(reverse: true);

    _scaleAnimation = Tween<double>(begin: 1.0, end: 1.15).animate(
      CurvedAnimation(parent: _pulseController, curve: Curves.easeInOut),
    );
  }

  @override
  void dispose() {
    _pulseController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    if (widget.isProcessing) {
      return Container(
        width: 84,
        height: 84,
        decoration: BoxDecoration(
          shape: BoxShape.circle,
          color: AppTheme.surfaceElevated,
          boxShadow: [
            BoxShadow(
              color: AppTheme.primaryGlow.withValues(alpha: 0.3),
              blurRadius: 20,
              spreadRadius: 2,
            ),
          ],
        ),
        child: const Center(
          child: SizedBox(
            width: 36,
            height: 36,
            child: CircularProgressIndicator(
              strokeWidth: 3,
              valueColor: AlwaysStoppedAnimation<Color>(AppTheme.primary),
            ),
          ),
        ),
      );
    }

    return Column(
      mainAxisSize: MainAxisSize.min,
      children: [
        GestureDetector(
          onTapDown: (_) => widget.onStart(),
          onTapUp: (_) => widget.onStop(),
          onTapCancel: () => widget.onStop(),
          child: AnimatedBuilder(
            animation: _scaleAnimation,
            builder: (context, child) {
              final scale = widget.isRecording ? _scaleAnimation.value : 1.0;
              return Transform.scale(
                scale: scale,
                child: Container(
                  width: 84,
                  height: 84,
                  decoration: BoxDecoration(
                    shape: BoxShape.circle,
                    gradient: widget.isRecording
                        ? const LinearGradient(
                            colors: [Color(0xFFEF4444), Color(0xFFDC2626)],
                            begin: Alignment.topLeft,
                            end: Alignment.bottomRight,
                          )
                        : AppTheme.primaryGradient,
                    boxShadow: [
                      BoxShadow(
                        color: widget.isRecording
                            ? const Color(0x88EF4444)
                            : AppTheme.primaryGlow,
                        blurRadius: widget.isRecording ? 28 : 20,
                        spreadRadius: widget.isRecording ? 6 : 2,
                      ),
                    ],
                  ),
                  child: Center(
                    child: Icon(
                      widget.isRecording ? Icons.mic : Icons.mic_none_rounded,
                      color: Colors.white,
                      size: 38,
                    ),
                  ),
                ),
              );
            },
          ),
        ),
        const SizedBox(height: 12),
        Text(
          widget.isRecording
              ? 'Recording... ${widget.durationSeconds}s (Release to send)'
              : 'Hold to speak',
          style: TextStyle(
            color: widget.isRecording ? AppTheme.accent : AppTheme.textSecondary,
            fontSize: 13,
            fontWeight: FontWeight.w500,
            letterSpacing: 0.3,
          ),
        ),
      ],
    );
  }
}
