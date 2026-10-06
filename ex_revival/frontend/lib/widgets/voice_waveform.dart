import 'dart:math';
import 'package:flutter/material.dart';
import 'package:frontend/core/theme/app_theme.dart';

class VoiceWaveformWidget extends StatefulWidget {
  final bool isActive;
  final double amplitude;
  final Color color;
  final double height;

  const VoiceWaveformWidget({
    super.key,
    required this.isActive,
    this.amplitude = 0.5,
    this.color = AppTheme.primary,
    this.height = 100,
  });

  @override
  State<VoiceWaveformWidget> createState() => _VoiceWaveformWidgetState();
}

class _VoiceWaveformWidgetState extends State<VoiceWaveformWidget> with SingleTickerProviderStateMixin {
  late AnimationController _controller;

  @override
  void initState() {
    super.initState();
    _controller = AnimationController(
      vsync: this,
      duration: const Duration(milliseconds: 1400),
    )..repeat();
  }

  @override
  void dispose() {
    _controller.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return AnimatedBuilder(
      animation: _controller,
      builder: (context, child) {
        return CustomPaint(
          size: Size(double.infinity, widget.height),
          painter: _WaveformPainter(
            animationValue: _controller.value,
            isActive: widget.isActive,
            amplitude: widget.amplitude,
            primaryColor: widget.color,
          ),
        );
      },
    );
  }
}

class _WaveformPainter extends CustomPainter {
  final double animationValue;
  final bool isActive;
  final double amplitude;
  final Color primaryColor;

  _WaveformPainter({
    required this.animationValue,
    required this.isActive,
    required this.amplitude,
    required this.primaryColor,
  });

  @override
  void paint(Canvas canvas, Size size) {
    final width = size.width;
    final height = size.height;
    final centerY = height / 2;

    const numBars = 36;
    final barWidth = (width / numBars) * 0.45;
    final spacing = width / numBars;

    final paint = Paint()
      ..strokeCap = StrokeCap.round
      ..strokeWidth = barWidth;

    for (int i = 0; i < numBars; i++) {
      final x = i * spacing + spacing / 2;
      double barHeight;

      if (isActive) {
        // Multi-frequency wave calculation with live amplitude reactivity
        final phase = animationValue * 2 * pi;
        final wave1 = sin(i * 0.35 + phase);
        final wave2 = cos(i * 0.2 - phase * 1.5);
        final dynamicFactor = (wave1 + wave2).abs() / 2;

        final liveAmp = max(0.15, amplitude);
        barHeight = (dynamicFactor * height * 0.8 * liveAmp) + 6.0;
      } else {
        // Gentle resting idle breathing animation
        final restingWave = sin(i * 0.25 + animationValue * pi);
        barHeight = 4.0 + restingWave.abs() * 8.0;
      }

      barHeight = min(barHeight, height * 0.95);

      paint.shader = LinearGradient(

        colors: [
          primaryColor.withOpacity(0.4),
          primaryColor,
          AppTheme.accent,
        ],
        begin: Alignment.topCenter,
        end: Alignment.bottomCenter,
      ).createShader(Rect.fromLTWH(x, centerY - barHeight / 2, barWidth, barHeight));

      canvas.drawLine(
        Offset(x, centerY - barHeight / 2),
        Offset(x, centerY + barHeight / 2),
        paint,
      );
    }
  }

  @override
  bool shouldRepaint(covariant _WaveformPainter oldDelegate) => true;
}
