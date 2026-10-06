import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'package:frontend/core/theme/app_theme.dart';
import 'package:frontend/core/routing/app_router.dart';
import 'package:frontend/core/config/app_config.dart';
import 'package:frontend/providers/auth_provider.dart';
import 'package:frontend/providers/revival_provider.dart';


class SettingsScreen extends StatelessWidget {
  const SettingsScreen({super.key});

  void _confirmDeleteRevival(BuildContext context) {
    final revivalProv = context.read<RevivalProvider>();
    final current = revivalProv.selectedRevival;
    if (current == null) return;

    showDialog(
      context: context,
      builder: (ctx) => AlertDialog(
        backgroundColor: AppTheme.surfaceElevated,
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(20)),
        title: Text('Delete ${current.name}?', style: const TextStyle(color: AppTheme.textPrimary)),
        content: const Text(
          'This will permanently delete this Revival profile, the reference voice recordings, and all memories.',
          style: TextStyle(color: AppTheme.textSecondary, fontSize: 14),
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(ctx),
            child: const Text('Cancel', style: TextStyle(color: AppTheme.textMuted)),
          ),
          ElevatedButton(
            style: ElevatedButton.styleFrom(backgroundColor: AppTheme.error),
            onPressed: () async {
              Navigator.pop(ctx);
              await revivalProv.deleteRevival(current.id);
              if (context.mounted) {
                Navigator.pushNamedAndRemoveUntil(context, AppRouter.home, (route) => false);
              }
            },
            child: const Text('Delete Permanently'),
          ),
        ],
      ),
    );
  }

  void _confirmSignOut(BuildContext context) {
    showDialog(
      context: context,
      builder: (ctx) => AlertDialog(
        backgroundColor: AppTheme.surfaceElevated,
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(20)),
        title: const Text('Sign Out?', style: TextStyle(color: AppTheme.textPrimary)),
        content: const Text(
          'Are you sure you want to sign out of EX REVIVAL?',
          style: TextStyle(color: AppTheme.textSecondary, fontSize: 14),
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(ctx),
            child: const Text('Cancel', style: TextStyle(color: AppTheme.textMuted)),
          ),
          ElevatedButton(
            onPressed: () async {
              Navigator.pop(ctx);
              await context.read<AuthProvider>().logout();
              if (context.mounted) {
                Navigator.pushNamedAndRemoveUntil(context, AppRouter.auth, (route) => false);
              }
            },
            child: const Text('Sign Out'),
          ),
        ],
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    final auth = context.watch<AuthProvider>();
    final revivalProv = context.watch<RevivalProvider>();
    final currentRevival = revivalProv.selectedRevival;

    return Scaffold(
      appBar: AppBar(title: const Text('Settings & Privacy')),
      body: ListView(
        padding: const EdgeInsets.symmetric(horizontal: 22, vertical: 16),
        children: [
          // Account Section
          const Text(
            'ACCOUNT',
            style: TextStyle(color: AppTheme.textMuted, fontSize: 12, fontWeight: FontWeight.bold, letterSpacing: 1.2),
          ),
          const SizedBox(height: 10),
          Container(
            decoration: BoxDecoration(
              color: AppTheme.surface,
              borderRadius: BorderRadius.circular(18),
              border: Border.all(color: const Color(0xFF24283A)),
            ),
            child: ListTile(
              leading: const Icon(Icons.account_circle_outlined, color: AppTheme.primary, size: 28),
              title: Text(
                auth.currentUser?.email ?? 'Unknown Account',
                style: const TextStyle(color: AppTheme.textPrimary, fontWeight: FontWeight.w600),
              ),
              subtitle: const Text('Authenticated with JWT', style: TextStyle(color: AppTheme.textMuted, fontSize: 12)),
              trailing: IconButton(
                icon: const Icon(Icons.logout_rounded, color: AppTheme.textSecondary),
                onPressed: () => _confirmSignOut(context),
              ),
            ),
          ),
          const SizedBox(height: 28),

          // Backend / AI Status Section
          const Text(
            'AI BACKEND STATUS',
            style: TextStyle(color: AppTheme.textMuted, fontSize: 12, fontWeight: FontWeight.bold, letterSpacing: 1.2),
          ),
          const SizedBox(height: 10),
          Container(
            padding: const EdgeInsets.all(18),
            decoration: BoxDecoration(
              color: AppTheme.surface,
              borderRadius: BorderRadius.circular(18),
              border: Border.all(color: const Color(0xFF24283A)),
            ),
            child: Column(
              children: [
                _buildStatusRow('Voice Engine', 'Chatterbox Multilingual V3', AppTheme.accent),
                const Divider(height: 18, color: Color(0xFF1E2235)),
                _buildStatusRow('Speech-to-Text', 'Whisper / Pluggable Adapter', AppTheme.primary),
                const Divider(height: 18, color: Color(0xFF1E2235)),
                _buildStatusRow('LLM Reasoning', 'Dynamic Character Prompting', AppTheme.success),
                const Divider(height: 18, color: Color(0xFF1E2235)),
                _buildStatusRow('API Endpoint', AppConfig.apiBaseUrl, AppTheme.textSecondary),
              ],
            ),
          ),
          const SizedBox(height: 28),

          // Privacy & Voice Ethics
          const Text(
            'PRIVACY & ETHICS',
            style: TextStyle(color: AppTheme.textMuted, fontSize: 12, fontWeight: FontWeight.bold, letterSpacing: 1.2),
          ),
          const SizedBox(height: 10),
          Container(
            padding: const EdgeInsets.all(18),
            decoration: BoxDecoration(
              color: AppTheme.surface,
              borderRadius: BorderRadius.circular(18),
              border: Border.all(color: const Color(0xFF24283A)),
            ),
            child: const Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  'Voice Ownership & Consent',
                  style: TextStyle(color: AppTheme.textPrimary, fontSize: 15, fontWeight: FontWeight.w600),
                ),
                SizedBox(height: 6),
                Text(
                  'EX REVIVAL enforces strict ethical voice recreation. All reference recordings must have owner consent. Audio files are stored securely and never used to train public foundational models.',
                  style: TextStyle(color: AppTheme.textSecondary, fontSize: 13, height: 1.4),
                ),
              ],
            ),
          ),
          const SizedBox(height: 28),

          // Data Management & Deletion
          if (currentRevival != null) ...[
            const Text(
              'REVIVAL MANAGEMENT',
              style: TextStyle(color: AppTheme.textMuted, fontSize: 12, fontWeight: FontWeight.bold, letterSpacing: 1.2),
            ),
            const SizedBox(height: 10),
            Container(
              decoration: BoxDecoration(
                color: AppTheme.surface,
                borderRadius: BorderRadius.circular(18),
                border: Border.all(color: const Color(0xFF24283A)),
              ),
              child: ListTile(
                leading: const Icon(Icons.delete_outline_rounded, color: AppTheme.error),
                title: Text(
                  'Delete "${currentRevival.name}"',
                  style: const TextStyle(color: AppTheme.error, fontWeight: FontWeight.w600),
                ),
                subtitle: const Text('Permanently erase character and voice audio', style: TextStyle(color: AppTheme.textMuted, fontSize: 12)),
                onTap: () => _confirmDeleteRevival(context),
              ),
            ),
            const SizedBox(height: 28),
          ],

          // App Info
          Center(
            child: Text(
              '${AppConfig.appName} v${AppConfig.version}\nDesigned for Voice-First Emotional Presence',
              style: const TextStyle(color: AppTheme.textMuted, fontSize: 12, height: 1.5),
              textAlign: TextAlign.center,
            ),
          ),
          const SizedBox(height: 20),
        ],
      ),
    );
  }

  Widget _buildStatusRow(String title, String value, Color statusColor) {
    return Row(
      mainAxisAlignment: MainAxisAlignment.spaceBetween,
      children: [
        Text(title, style: const TextStyle(color: AppTheme.textSecondary, fontSize: 13)),
        Row(
          children: [
            Container(
              width: 6,
              height: 6,
              decoration: BoxDecoration(shape: BoxShape.circle, color: statusColor),
            ),
            const SizedBox(width: 8),
            Text(
              value,
              style: TextStyle(color: AppTheme.textPrimary, fontSize: 13, fontWeight: FontWeight.w600),
            ),
          ],
        ),
      ],
    );
  }
}
