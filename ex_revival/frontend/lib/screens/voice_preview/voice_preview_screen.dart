import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'package:frontend/core/theme/app_theme.dart';
import 'package:frontend/core/routing/app_router.dart';
import 'package:frontend/core/constants/app_constants.dart';
import 'package:frontend/providers/revival_provider.dart';
import 'package:frontend/providers/conversation_provider.dart';
import 'package:frontend/widgets/audio_player.dart';

class VoicePreviewScreen extends StatefulWidget {
  const VoicePreviewScreen({super.key});

  @override
  State<VoicePreviewScreen> createState() => _VoicePreviewScreenState();
}

class _VoicePreviewScreenState extends State<VoicePreviewScreen> {
  String _selectedPhrase = AppConstants.samplePhrases.first;
  final _customPhraseController = TextEditingController();

  @override
  void dispose() {
    _customPhraseController.dispose();
    super.dispose();
  }

  Future<void> _generatePreview() async {
    final phrase = _customPhraseController.text.trim().isNotEmpty
        ? _customPhraseController.text.trim()
        : _selectedPhrase;
    await context.read<RevivalProvider>().previewVoice(phrase);
  }

  Future<void> _startConversation() async {
    final revival = context.read<RevivalProvider>().selectedRevival;
    if (revival == null) return;

    final convProv = context.read<ConversationProvider>();
    await convProv.startNewConversation(revival.id, title: 'Chat with ${revival.name}');

    if (mounted) {
      Navigator.pushNamed(context, AppRouter.conversation);
    }
  }

  @override
  Widget build(BuildContext context) {
    final revivalProv = context.watch<RevivalProvider>();
    final current = revivalProv.selectedRevival;
    final isLoading = revivalProv.isPreviewLoading;
    final previewResult = revivalProv.previewResult;

    return Scaffold(
      appBar: AppBar(title: Text(current != null ? '${current.name} • Voice Preview' : 'Voice Preview')),
      body: SingleChildScrollView(
        padding: const EdgeInsets.all(24),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            const Text(
              'Listen to Synthesized Voice',
              style: TextStyle(
                color: AppTheme.textPrimary,
                fontSize: 22,
                fontWeight: FontWeight.bold,
                letterSpacing: -0.3,
              ),
            ),
            const SizedBox(height: 8),
            const Text(
              'Select or type a phrase to test Chatterbox voice cloning using your authorized reference sample.',
              style: TextStyle(color: AppTheme.textSecondary, fontSize: 14, height: 1.4),
            ),
            const SizedBox(height: 24),

            // Preset Phrases
            const Text(
              'Select Sample Phrase',
              style: TextStyle(color: AppTheme.textPrimary, fontSize: 15, fontWeight: FontWeight.w600),
            ),
            const SizedBox(height: 12),

            ...AppConstants.samplePhrases.map((phrase) {
              final isSelected = _selectedPhrase == phrase && _customPhraseController.text.isEmpty;
              return Container(
                margin: const EdgeInsets.only(bottom: 10),
                decoration: BoxDecoration(
                  color: isSelected ? AppTheme.primary.withValues(alpha: 0.15) : AppTheme.surfaceElevated,
                  borderRadius: BorderRadius.circular(16),
                  border: Border.all(
                    color: isSelected ? AppTheme.primary : const Color(0xFF282C40),
                    width: 1.2,
                  ),
                ),
                child: ListTile(
                  title: Text(
                    phrase,
                    style: TextStyle(
                      color: isSelected ? AppTheme.textPrimary : AppTheme.textSecondary,
                      fontSize: 14,
                    ),
                  ),
                  trailing: isSelected
                      ? const Icon(Icons.check_circle_rounded, color: AppTheme.primary, size: 20)
                      : null,
                  onTap: () {
                    setState(() {
                      _selectedPhrase = phrase;
                      _customPhraseController.clear();
                    });
                  },
                ),
              );
            }),
            const SizedBox(height: 16),

            // Custom Phrase Option
            TextFormField(
              controller: _customPhraseController,
              style: const TextStyle(color: AppTheme.textPrimary),
              decoration: const InputDecoration(
                labelText: 'Or Type Custom Preview Phrase',
                hintText: 'e.g. Good morning! Did you sleep well?',
              ),
              onChanged: (val) {
                if (val.isNotEmpty) setState(() {});
              },
            ),
            const SizedBox(height: 28),

            // Generate Button
            ElevatedButton.icon(
              onPressed: isLoading ? null : _generatePreview,
              icon: const Icon(Icons.graphic_eq_rounded, size: 20),
              label: Text(isLoading ? 'Synthesizing Audio...' : 'Generate Voice Preview'),
              style: ElevatedButton.styleFrom(
                backgroundColor: AppTheme.surfaceElevated,
                foregroundColor: AppTheme.accent,
                side: const BorderSide(color: AppTheme.accent, width: 1.2),
              ),
            ),
            const SizedBox(height: 24),

            // Preview Player
            if (previewResult != null) ...[
              Container(
                padding: const EdgeInsets.all(20),
                decoration: BoxDecoration(
                  color: AppTheme.surface,
                  borderRadius: BorderRadius.circular(20),
                  border: Border.all(color: AppTheme.accent.withValues(alpha: 0.4), width: 1.2),
                  boxShadow: [
                    BoxShadow(
                      color: AppTheme.accentGlow.withValues(alpha: 0.2),
                      blurRadius: 20,
                    ),
                  ],
                ),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Row(
                      mainAxisAlignment: MainAxisAlignment.spaceBetween,
                      children: [
                        const Text(
                          'Preview Result',
                          style: TextStyle(
                            color: AppTheme.textPrimary,
                            fontSize: 15,
                            fontWeight: FontWeight.bold,
                          ),
                        ),
                        Text(
                          'Latency: ${previewResult.latencyMs}ms',
                          style: const TextStyle(color: AppTheme.textMuted, fontSize: 12),
                        ),
                      ],
                    ),
                    const SizedBox(height: 12),
                    Text(
                      '"${previewResult.phrase}"',
                      style: const TextStyle(
                        color: AppTheme.textSecondary,
                        fontSize: 14,
                        fontStyle: FontStyle.italic,
                      ),
                    ),
                    const SizedBox(height: 16),
                    AudioPlayerBarWidget(
                      audioUrl: previewResult.audioUrl,
                      title: '${current?.name ?? "Character"} Voice Preview',
                    ),
                  ],
                ),
              ),
              const SizedBox(height: 32),
            ],

            // Start Conversation CTA
            ElevatedButton.icon(
              onPressed: _startConversation,
              icon: const Icon(Icons.forum_rounded, size: 20),
              label: const Text('Start Live Conversation'),
            ),
          ],
        ),
      ),
    );
  }
}
