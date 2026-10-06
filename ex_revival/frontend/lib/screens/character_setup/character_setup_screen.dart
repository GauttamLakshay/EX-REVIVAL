import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'package:frontend/core/theme/app_theme.dart';
import 'package:frontend/core/routing/app_router.dart';
import 'package:frontend/providers/revival_provider.dart';

class CharacterSetupScreen extends StatefulWidget {
  const CharacterSetupScreen({super.key});

  @override
  State<CharacterSetupScreen> createState() => _CharacterSetupScreenState();
}

class _CharacterSetupScreenState extends State<CharacterSetupScreen> {
  final _personalityController = TextEditingController();
  final _speakingStyleController = TextEditingController();
  final _relationshipContextController = TextEditingController();

  final List<String> _personalityPresets = [
    'Funny + caring',
    'Thoughtful, calm, and deeply supportive',
    'Playful, sarcastic, and energetic',
    'Wise, affectionate, and grounded',
  ];

  final List<String> _stylePresets = [
    'Casual, natural spoken tone with warm phrasing',
    'Fast-paced, conversational, uses modern slang',
    'Gentle, soothing cadence with comforting words',
    'Expressive, enthusiastic, and direct',
  ];

  @override
  void initState() {
    super.initState();
    final current = context.read<RevivalProvider>().selectedRevival;
    if (current != null) {
      _personalityController.text = current.personality.isNotEmpty
          ? current.personality
          : 'Funny + caring';
      _speakingStyleController.text = current.speakingStyle.isNotEmpty
          ? current.speakingStyle
          : 'Casual, warm, and natural';
      _relationshipContextController.text = current.relationshipContext.isNotEmpty
          ? current.relationshipContext
          : 'Best friend from university';
    }
  }

  @override
  void dispose() {
    _personalityController.dispose();
    _speakingStyleController.dispose();
    _relationshipContextController.dispose();
    super.dispose();
  }

  Future<void> _saveAndPreview() async {
    final revivalProv = context.read<RevivalProvider>();
    final current = revivalProv.selectedRevival;
    if (current == null) return;

    await revivalProv.updateCharacterConfig(
      revivalId: current.id,
      personality: _personalityController.text.trim(),
      speakingStyle: _speakingStyleController.text.trim(),
      relationshipContext: _relationshipContextController.text.trim(),
    );

    if (mounted) {
      Navigator.pushNamed(context, AppRouter.voicePreview);
    }
  }

  @override
  Widget build(BuildContext context) {
    final revivalProv = context.watch<RevivalProvider>();
    final current = revivalProv.selectedRevival;
    final isSaving = revivalProv.status == RevivalStatus.saving;

    return Scaffold(
      appBar: AppBar(title: Text(current != null ? '${current.name} • Character Setup' : 'Character Setup')),
      body: SingleChildScrollView(
        padding: const EdgeInsets.all(24),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            const Text(
              'Personality & Speaking Nuance',
              style: TextStyle(
                color: AppTheme.textPrimary,
                fontSize: 22,
                fontWeight: FontWeight.bold,
                letterSpacing: -0.3,
              ),
            ),
            const SizedBox(height: 8),
            const Text(
              'Shape how your Revival character speaks, reacts, and remembers your shared bond.',
              style: TextStyle(color: AppTheme.textSecondary, fontSize: 14, height: 1.4),
            ),
            const SizedBox(height: 28),

            // Personality Field
            const Text(
              'Personality Traits',
              style: TextStyle(color: AppTheme.textPrimary, fontSize: 15, fontWeight: FontWeight.w600),
            ),
            const SizedBox(height: 8),
            TextFormField(
              controller: _personalityController,
              maxLines: 2,
              style: const TextStyle(color: AppTheme.textPrimary),
              decoration: const InputDecoration(
                hintText: 'e.g. Funny, compassionate, witty, never judgmental',
              ),
            ),
            const SizedBox(height: 8),
            Wrap(
              spacing: 8,
              runSpacing: 8,
              children: _personalityPresets.map((preset) {
                return ActionChip(
                  label: Text(preset, style: const TextStyle(fontSize: 12, color: AppTheme.textPrimary)),
                  backgroundColor: AppTheme.surfaceElevated,
                  side: const BorderSide(color: Color(0xFF2A2E44)),
                  onPressed: () => setState(() => _personalityController.text = preset),
                );
              }).toList(),
            ),
            const SizedBox(height: 24),

            // Speaking Style Field
            const Text(
              'Speaking Style & Cadence',
              style: TextStyle(color: AppTheme.textPrimary, fontSize: 15, fontWeight: FontWeight.w600),
            ),
            const SizedBox(height: 8),
            TextFormField(
              controller: _speakingStyleController,
              maxLines: 2,
              style: const TextStyle(color: AppTheme.textPrimary),
              decoration: const InputDecoration(
                hintText: 'e.g. Speaks casually, uses short expressive sentences, gentle chuckles',
              ),
            ),
            const SizedBox(height: 8),
            Wrap(
              spacing: 8,
              runSpacing: 8,
              children: _stylePresets.map((preset) {
                return ActionChip(
                  label: Text(preset, style: const TextStyle(fontSize: 12, color: AppTheme.textPrimary)),
                  backgroundColor: AppTheme.surfaceElevated,
                  side: const BorderSide(color: Color(0xFF2A2E44)),
                  onPressed: () => setState(() => _speakingStyleController.text = preset),
                );
              }).toList(),
            ),
            const SizedBox(height: 24),

            // Relationship Context Field
            const Text(
              'Relationship Context',
              style: TextStyle(color: AppTheme.textPrimary, fontSize: 15, fontWeight: FontWeight.w600),
            ),
            const SizedBox(height: 8),
            TextFormField(
              controller: _relationshipContextController,
              maxLines: 3,
              style: const TextStyle(color: AppTheme.textPrimary),
              decoration: const InputDecoration(
                hintText: 'e.g. Lifelong childhood best friend; shared an apartment during our first jobs; always reminisces about late night road trips',
              ),
            ),
            const SizedBox(height: 36),

            // Next Button
            ElevatedButton(
              onPressed: isSaving ? null : _saveAndPreview,
              child: isSaving
                  ? const SizedBox(
                      width: 20,
                      height: 20,
                      child: CircularProgressIndicator(strokeWidth: 2, color: Colors.white),
                    )
                  : const Text('Save & Preview Voice'),
            ),
          ],
        ),
      ),
    );
  }
}
