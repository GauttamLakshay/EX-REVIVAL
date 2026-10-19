import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'package:frontend/core/theme/app_theme.dart';
import 'package:frontend/providers/conversation_provider.dart';
import 'package:frontend/providers/revival_provider.dart';
import 'package:frontend/widgets/voice_waveform.dart';
import 'package:frontend/widgets/record_button.dart';
import 'package:frontend/widgets/message_bubble.dart';
import 'package:frontend/widgets/loading_states.dart';

class ConversationScreen extends StatefulWidget {
  const ConversationScreen({super.key});

  @override
  State<ConversationScreen> createState() => _ConversationScreenState();
}

class _ConversationScreenState extends State<ConversationScreen> {
  final ScrollController _scrollController = ScrollController();
  final TextEditingController _textInputController = TextEditingController();
  bool _showTextInput = false;

  int _lastMessageCount = 0;

  @override
  void dispose() {
    _scrollController.dispose();
    _textInputController.dispose();
    super.dispose();
  }

  void _scrollToBottom() {
    WidgetsBinding.instance.addPostFrameCallback((_) {
      if (_scrollController.hasClients) {
        _scrollController.animateTo(
          _scrollController.position.maxScrollExtent,
          duration: const Duration(milliseconds: 300),
          curve: Curves.easeOut,
        );
      }
    });
  }

  Future<void> _submitTypedMessage() async {
    final text = _textInputController.text.trim();
    if (text.isEmpty) return;

    _textInputController.clear();
    setState(() => _showTextInput = false);

    final convProv = context.read<ConversationProvider>();
    await convProv.submitTurn(clientTranscript: text);
    _scrollToBottom();
  }

  @override
  Widget build(BuildContext context) {
    final revival = context.watch<RevivalProvider>().selectedRevival;
    final conv = context.watch<ConversationProvider>();
    final messages = conv.messages;
    final state = conv.state;

    // Scroll down only when new messages are added
    if (messages.length > _lastMessageCount) {
      _lastMessageCount = messages.length;
      _scrollToBottom();
    }

    final characterName = revival?.name ?? 'Alex';

    return Scaffold(
      appBar: AppBar(
        title: Column(
          children: [
            Text(
              characterName,
              style: const TextStyle(fontSize: 18, fontWeight: FontWeight.bold),
            ),
            const SizedBox(height: 2),
            ConversationStateIndicatorWidget(
              state: state,
              errorMessage: conv.errorMessage,
              onRetry: () => conv.clearError(),
            ),
          ],
        ),
        actions: [
          IconButton(
            icon: Icon(
              _showTextInput ? Icons.mic_rounded : Icons.keyboard_rounded,
              color: AppTheme.accent,
            ),
            tooltip: _showTextInput ? 'Voice Input' : 'Keyboard Input',
            onPressed: () {
              setState(() {
                _showTextInput = !_showTextInput;
              });
            },
          ),
          if (conv.isSpeaking)
            IconButton(
              icon: const Icon(Icons.stop_circle_outlined, color: AppTheme.error),
              tooltip: 'Stop Voice',
              onPressed: () => conv.stopPlayback(),
            ),
        ],
      ),
      body: Column(
        children: [
          // Upper Visual Stage: Avatar + Real-Time Audio-Reactive Waveform
          Container(
            padding: const EdgeInsets.symmetric(vertical: 20, horizontal: 24),
            decoration: BoxDecoration(
              gradient: RadialGradient(
                center: const Alignment(0, -0.4),
                radius: 1.2,
                colors: [
                  conv.isSpeaking
                      ? AppTheme.accentGlow.withValues(alpha: 0.3)
                      : (conv.isRecording
                          ? const Color(0x33EF4444)
                          : AppTheme.primaryGlow.withValues(alpha: 0.2)),
                  Colors.transparent,
                ],
              ),
            ),
            child: Column(
              children: [
                // Glowing Avatar
                Container(
                  width: 72,
                  height: 72,
                  decoration: BoxDecoration(
                    shape: BoxShape.circle,
                    gradient: conv.isSpeaking
                        ? const LinearGradient(colors: [Color(0xFF06B6D4), Color(0xFF10B981)])
                        : (conv.isRecording
                            ? const LinearGradient(colors: [Color(0xFFEF4444), Color(0xFFF97316)])
                            : AppTheme.primaryGradient),
                    boxShadow: [
                      BoxShadow(
                        color: conv.isSpeaking
                            ? AppTheme.accentGlow
                            : (conv.isRecording ? const Color(0x88EF4444) : AppTheme.primaryGlow),
                        blurRadius: 28,
                        spreadRadius: 3,
                      ),
                    ],
                  ),
                  child: Center(
                    child: Text(
                      characterName.isNotEmpty ? characterName[0].toUpperCase() : 'A',
                      style: const TextStyle(
                        color: Colors.white,
                        fontSize: 30,
                        fontWeight: FontWeight.bold,
                      ),
                    ),
                  ),
                ),
                const SizedBox(height: 16),

                // Fluid Audio Waveform
                VoiceWaveformWidget(
                  isActive: conv.isRecording || conv.isSpeaking,
                  amplitude: conv.isRecording ? conv.currentAmplitude : 0.65,
                  color: conv.isSpeaking
                      ? AppTheme.accent
                      : (conv.isRecording ? const Color(0xFFEF4444) : AppTheme.primary),
                  height: 64,
                ),
              ],
            ),
          ),

          const Divider(height: 1, color: Color(0xFF1E2235)),

          // Messages Timeline / Transcript View
          Expanded(
            child: messages.isEmpty
                ? Center(
                    child: Padding(
                      padding: const EdgeInsets.symmetric(horizontal: 36),
                      child: Column(
                        mainAxisSize: MainAxisSize.min,
                        children: [
                          Icon(
                            Icons.mic_none_rounded,
                            color: AppTheme.textMuted.withValues(alpha: 0.3),
                            size: 54,
                          ),
                          const SizedBox(height: 12),
                          Text(
                            'Hold the microphone below to talk to $characterName',
                            style: const TextStyle(
                              color: AppTheme.textSecondary,
                              fontSize: 14,
                              height: 1.4,
                            ),
                            textAlign: TextAlign.center,
                          ),
                        ],
                      ),
                    ),
                  )
                : ListView.builder(
                    controller: _scrollController,
                    padding: const EdgeInsets.symmetric(vertical: 16),
                    itemCount: messages.length,
                    itemBuilder: (context, index) {
                      final msg = messages[index];
                      return MessageBubbleWidget(
                        message: msg,
                        onPlayAudio: msg.hasAudio ? () => conv.playMessageAudio(msg) : null,
                      );
                    },
                  ),
          ),

          // Lower Controls Stage
          Container(
            padding: const EdgeInsets.fromLTRB(20, 16, 20, 24),
            decoration: const BoxDecoration(
              color: AppTheme.surface,
              border: Border(top: BorderSide(color: Color(0xFF1E2235), width: 1)),
            ),
            child: SafeArea(
              top: false,
              child: _showTextInput
                  ? Row(
                      children: [
                        Expanded(
                          child: TextField(
                            controller: _textInputController,
                            style: const TextStyle(color: AppTheme.textPrimary),
                            decoration: const InputDecoration(
                              hintText: 'Type your message...',
                              contentPadding: EdgeInsets.symmetric(horizontal: 18, vertical: 14),
                            ),
                            onSubmitted: (_) => _submitTypedMessage(),
                          ),
                        ),
                        const SizedBox(width: 12),
                        IconButton(
                          icon: const Icon(Icons.send_rounded, color: AppTheme.accent),
                          onPressed: _submitTypedMessage,
                        ),
                      ],
                    )
                  : Center(
                      child: RecordButtonWidget(
                        isRecording: conv.isRecording,
                        isProcessing: conv.isProcessing,
                        durationSeconds: conv.recordingDuration,
                        onStart: () => conv.startRecording(),
                        onStop: () => conv.stopAndSubmitRecording(),
                      ),
                    ),
            ),
          ),
        ],
      ),
    );
  }
}
