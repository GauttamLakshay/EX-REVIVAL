import 'dart:async';
import 'dart:typed_data';
import 'package:flutter/material.dart';

import 'package:file_picker/file_picker.dart';
import 'package:provider/provider.dart';
import 'package:frontend/core/theme/app_theme.dart';
import 'package:frontend/core/routing/app_router.dart';
import 'package:frontend/core/constants/app_constants.dart';
import 'package:frontend/providers/revival_provider.dart';
import 'package:frontend/services/audio_recorder_service.dart';


class CreateRevivalScreen extends StatefulWidget {
  const CreateRevivalScreen({super.key});

  @override
  State<CreateRevivalScreen> createState() => _CreateRevivalScreenState();
}

class _CreateRevivalScreenState extends State<CreateRevivalScreen> {
  final _formKey = GlobalKey<FormState>();
  final _nameController = TextEditingController();
  String _selectedLanguage = 'en';

  Uint8List? _audioBytes;
  String? _audioFilename;
  bool _isRecording = false;
  int _recordDuration = 0;
  StreamSubscription<int>? _durationSub;

  bool _isAuthorizedConfirmed = false;

  @override
  void initState() {
    super.initState();
    _durationSub = audioRecorderService.durationStream.listen((sec) {
      if (mounted) setState(() => _recordDuration = sec);
    });
  }

  @override
  void dispose() {
    _durationSub?.cancel();
    _nameController.dispose();
    super.dispose();
  }

  Future<void> _pickAudioFile() async {
    try {
      final files = await FilePicker.pickFiles(
        type: FileType.custom,
        allowedExtensions: ['wav', 'mp3', 'm4a', 'ogg'],
      );

      if (files.isNotEmpty) {
        final file = files.first;
        final bytes = await file.xFile.readAsBytes();
        setState(() {
          _audioBytes = bytes;
          _audioFilename = file.name;
        });
      }
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('Failed to select file: $e'), backgroundColor: AppTheme.error),
        );
      }
    }
  }

  Future<void> _toggleRecording() async {
    if (_isRecording) {
      final bytes = await audioRecorderService.stopRecording();
      setState(() {
        _isRecording = false;
        if (bytes != null && bytes.isNotEmpty) {
          _audioBytes = bytes;
          _audioFilename = 'recorded_voice.wav';
        }
      });
    } else {
      try {
        await audioRecorderService.startRecording();
        setState(() {
          _isRecording = true;
          _audioBytes = null;
          _audioFilename = null;
        });
      } catch (e) {
        if (mounted) {
          ScaffoldMessenger.of(context).showSnackBar(
            SnackBar(content: Text(e.toString()), backgroundColor: AppTheme.error),
          );
        }
      }
    }
  }


  void _showAuthorizationModal(VoidCallback onConfirmed) {
    showModalBottomSheet(
      context: context,
      backgroundColor: AppTheme.surfaceElevated,
      shape: const RoundedRectangleBorder(
        borderRadius: BorderRadius.vertical(top: Radius.circular(24)),
      ),
      builder: (context) {
        return Padding(
          padding: const EdgeInsets.all(28),
          child: Column(
            mainAxisSize: MainAxisSize.min,
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: [
              Center(
                child: Container(
                  width: 44,
                  height: 4,
                  decoration: BoxDecoration(
                    color: AppTheme.textMuted,
                    borderRadius: BorderRadius.circular(2),
                  ),
                ),
              ),
              const SizedBox(height: 20),
              const Row(
                children: [
                  Icon(Icons.verified_user_outlined, color: AppTheme.accent, size: 28),
                  SizedBox(width: 12),
                  Text(

                    'Voice Authorization',
                    style: TextStyle(
                      color: AppTheme.textPrimary,
                      fontSize: 20,
                      fontWeight: FontWeight.bold,
                    ),
                  ),
                ],
              ),
              const SizedBox(height: 16),
              const Text(
                'I confirm that I am authorized to use this reference voice in EX REVIVAL. I possess legal consent or rights to synthesize and clone speech from this audio recording.',
                style: TextStyle(
                  color: AppTheme.textSecondary,
                  fontSize: 14,
                  height: 1.45,
                ),
              ),
              const SizedBox(height: 28),
              ElevatedButton(
                onPressed: () {
                  Navigator.pop(context);
                  onConfirmed();
                },
                child: const Text('I Confirm & Authorize'),
              ),
            ],
          ),
        );
      },
    );
  }

  Future<void> _submit() async {
    if (!_formKey.currentState!.validate()) return;

    if (_audioBytes == null) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(
          content: Text('Please record or upload a reference voice sample.'),
          backgroundColor: AppTheme.warning,
        ),
      );
      return;
    }

    if (!_isAuthorizedConfirmed) {
      _showAuthorizationModal(() {
        setState(() => _isAuthorizedConfirmed = true);
        _proceedCreation();
      });
      return;
    }

    _proceedCreation();
  }

  Future<void> _proceedCreation() async {
    final revivalProv = context.read<RevivalProvider>();

    // 1. Create Revival
    final revival = await revivalProv.createRevival(
      name: _nameController.text.trim(),
      language: _selectedLanguage,
      voiceAuthorized: true,
    );

    if (revival == null) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text(revivalProv.errorMessage ?? 'Failed to create Revival. Please try again.'),
            backgroundColor: AppTheme.error,
          ),
        );
      }
      return;
    }

    // 2. Upload Voice Sample
    final uploadSuccess = await revivalProv.uploadVoice(
      revivalId: revival.id,
      audioBytes: _audioBytes!,
      filename: _audioFilename ?? 'reference.wav',
      voiceAuthorized: true,
    );

    if (uploadSuccess && mounted) {
      Navigator.pushReplacementNamed(context, AppRouter.characterSetup);
    } else if (mounted) {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text(revivalProv.errorMessage ?? 'Failed to upload voice sample.'),
          backgroundColor: AppTheme.error,
        ),
      );
    }
  }

  @override
  Widget build(BuildContext context) {
    final revivalProv = context.watch<RevivalProvider>();
    final isSaving = revivalProv.status == RevivalStatus.saving;

    return Scaffold(
      appBar: AppBar(title: const Text('Create Revival')),
      body: SingleChildScrollView(
        padding: const EdgeInsets.all(24),
        child: Form(
          key: _formKey,
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: [
              const Text(
                'Identity & Reference Voice',
                style: TextStyle(
                  color: AppTheme.textPrimary,
                  fontSize: 22,
                  fontWeight: FontWeight.bold,
                  letterSpacing: -0.3,
                ),
              ),
              const SizedBox(height: 8),
              const Text(
                'Provide the character name and a clear audio recording (3 to 30 seconds) of their speaking voice.',
                style: TextStyle(color: AppTheme.textSecondary, fontSize: 14, height: 1.4),
              ),
              const SizedBox(height: 28),

              // Name Field
              TextFormField(
                controller: _nameController,
                style: const TextStyle(color: AppTheme.textPrimary),
                decoration: const InputDecoration(
                  labelText: 'Character Name',
                  hintText: 'e.g. Alex, Mom, Maya',
                  prefixIcon: Icon(Icons.person_outline_rounded, color: AppTheme.textMuted),
                ),
                validator: (val) {
                  if (val == null || val.trim().isEmpty) return 'Character name is required';
                  return null;
                },
              ),
              const SizedBox(height: 20),

              // Language Selector
              DropdownButtonFormField<String>(
                initialValue: _selectedLanguage,
                dropdownColor: AppTheme.surfaceElevated,

                decoration: const InputDecoration(
                  labelText: 'Primary Language',
                  prefixIcon: Icon(Icons.language_rounded, color: AppTheme.textMuted),
                ),
                items: AppConstants.supportedLanguages.map((lang) {
                  return DropdownMenuItem(
                    value: lang,
                    child: Text(
                      lang == 'en'
                          ? 'English'
                          : (lang == 'hi'
                              ? 'Hindi / Hinglish'
                              : (lang == 'es' ? 'Spanish' : lang.toUpperCase())),
                      style: const TextStyle(color: AppTheme.textPrimary),
                    ),
                  );
                }).toList(),
                onChanged: (val) {
                  if (val != null) setState(() => _selectedLanguage = val);
                },
              ),
              const SizedBox(height: 32),

              // Voice Input Section
              const Text(
                'Reference Voice Sample',
                style: TextStyle(color: AppTheme.textPrimary, fontSize: 16, fontWeight: FontWeight.bold),
              ),
              const SizedBox(height: 12),

              Container(
                padding: const EdgeInsets.all(20),
                decoration: BoxDecoration(
                  color: AppTheme.surfaceElevated,
                  borderRadius: BorderRadius.circular(20),
                  border: Border.all(
                    color: _audioBytes != null ? AppTheme.accent : const Color(0xFF292D3E),
                    width: 1.2,
                  ),
                ),
                child: Column(
                  children: [
                    if (_audioBytes != null) ...[
                      Row(
                        children: [
                          const Icon(Icons.check_circle_rounded, color: AppTheme.success, size: 28),
                          const SizedBox(width: 12),
                          Expanded(
                            child: Column(
                              crossAxisAlignment: CrossAxisAlignment.start,
                              children: [
                                Text(
                                  _audioFilename ?? 'Voice sample selected',
                                  style: const TextStyle(
                                    color: AppTheme.textPrimary,
                                    fontSize: 14,
                                    fontWeight: FontWeight.w600,
                                  ),
                                  maxLines: 1,
                                  overflow: TextOverflow.ellipsis,
                                ),
                                const SizedBox(height: 2),
                                Text(
                                  'Ready for Chatterbox normalization (${(_audioBytes!.length / 1024).toStringAsFixed(1)} KB)',
                                  style: const TextStyle(color: AppTheme.textMuted, fontSize: 12),
                                ),
                              ],
                            ),
                          ),
                          IconButton(
                            icon: const Icon(Icons.close, color: AppTheme.textMuted),
                            onPressed: () => setState(() {
                              _audioBytes = null;
                              _audioFilename = null;
                            }),
                          ),
                        ],
                      ),
                      const SizedBox(height: 16),
                    ],
                    Row(
                      children: [
                        // Record Voice Button
                        Expanded(
                          child: OutlinedButton.icon(
                            onPressed: _toggleRecording,
                            icon: Icon(
                              _isRecording ? Icons.stop_circle_rounded : Icons.mic_rounded,
                              color: _isRecording ? AppTheme.error : AppTheme.primary,
                            ),
                            label: Text(
                              _isRecording ? 'Stop (${_recordDuration}s)' : 'Record Voice',
                              style: TextStyle(
                                color: _isRecording ? AppTheme.error : AppTheme.textPrimary,
                              ),
                            ),
                            style: OutlinedButton.styleFrom(
                              padding: const EdgeInsets.symmetric(vertical: 14),
                              side: BorderSide(
                                color: _isRecording ? AppTheme.error : AppTheme.primary.withValues(alpha: 0.5),
                              ),
                              shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(14)),
                            ),
                          ),
                        ),
                        const SizedBox(width: 12),
                        // Upload Audio Button
                        Expanded(
                          child: OutlinedButton.icon(
                            onPressed: _pickAudioFile,
                            icon: const Icon(Icons.upload_file_rounded, color: AppTheme.accent),
                            label: const Text('Upload File', style: TextStyle(color: AppTheme.textPrimary)),
                            style: OutlinedButton.styleFrom(
                              padding: const EdgeInsets.symmetric(vertical: 14),
                              side: BorderSide(color: AppTheme.accent.withValues(alpha: 0.5)),
                              shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(14)),
                            ),
                          ),
                        ),
                      ],
                    ),
                  ],
                ),
              ),
              const SizedBox(height: 24),

              // Authorization Checkbox per Section 15
              CheckboxListTile(
                value: _isAuthorizedConfirmed,
                onChanged: (val) => setState(() => _isAuthorizedConfirmed = val ?? false),
                activeColor: AppTheme.primary,
                contentPadding: EdgeInsets.zero,
                controlAffinity: ListTileControlAffinity.leading,
                title: const Text(
                  'I confirm that I am authorized to use this reference voice in EX REVIVAL.',
                  style: TextStyle(color: AppTheme.textSecondary, fontSize: 13, height: 1.3),
                ),
              ),
              const SizedBox(height: 32),

              // Submit Button
              ElevatedButton(
                onPressed: isSaving ? null : _submit,
                child: isSaving
                    ? const Row(
                        mainAxisAlignment: MainAxisAlignment.center,
                        children: [
                          SizedBox(
                            width: 20,
                            height: 20,
                            child: CircularProgressIndicator(strokeWidth: 2, color: Colors.white),
                          ),
                          SizedBox(width: 12),
                          Text('Synthesizing Profile...'),
                        ],
                      )
                    : const Text('Continue to Character Setup'),
              ),
            ],
          ),
        ),
      ),
    );
  }
}
