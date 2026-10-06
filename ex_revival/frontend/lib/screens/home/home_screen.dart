import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'package:frontend/core/theme/app_theme.dart';
import 'package:frontend/core/routing/app_router.dart';
import 'package:frontend/providers/auth_provider.dart';
import 'package:frontend/providers/revival_provider.dart';
import 'package:frontend/providers/conversation_provider.dart';
import 'package:frontend/widgets/revival_card.dart';

class HomeScreen extends StatefulWidget {
  const HomeScreen({super.key});

  @override
  State<HomeScreen> createState() => _HomeScreenState();
}

class _HomeScreenState extends State<HomeScreen> {
  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addPostFrameCallback((_) {
      context.read<RevivalProvider>().loadRevivals();
    });
  }

  @override
  Widget build(BuildContext context) {
    final auth = context.watch<AuthProvider>();
    final revivalProv = context.watch<RevivalProvider>();
    final revivals = revivalProv.revivals;
    final isLoading = revivalProv.status == RevivalStatus.loading;

    final userEmail = auth.currentUser?.email ?? 'Explorer';
    final userName = userEmail.contains('@') ? userEmail.split('@').first : userEmail;

    return Scaffold(
      appBar: AppBar(
        title: const Text('EX REVIVAL'),
        actions: [
          IconButton(
            icon: const Icon(Icons.settings_outlined),
            onPressed: () => Navigator.pushNamed(context, AppRouter.settings),
          ),
        ],
      ),
      body: RefreshIndicator(
        onRefresh: () => revivalProv.loadRevivals(),
        color: AppTheme.accent,
        backgroundColor: AppTheme.surfaceElevated,
        child: CustomScrollView(
          physics: const AlwaysScrollableScrollPhysics(),
          slivers: [
            SliverToBoxAdapter(
              child: Padding(
                padding: const EdgeInsets.fromLTRB(22, 16, 22, 24),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    // Greeting & Subtitle
                    Text(
                      'Welcome back, $userName',
                      style: const TextStyle(
                        color: AppTheme.textPrimary,
                        fontSize: 24,
                        fontWeight: FontWeight.bold,
                        letterSpacing: -0.3,
                      ),
                    ),
                    const SizedBox(height: 6),
                    const Text(
                      'Select a Revival character to engage in spoken conversation.',
                      style: TextStyle(
                        color: AppTheme.textSecondary,
                        fontSize: 14,
                      ),
                    ),
                    const SizedBox(height: 24),

                    // Create Revival Banner / CTA
                    Container(
                      padding: const EdgeInsets.all(22),
                      decoration: BoxDecoration(
                        gradient: AppTheme.darkCardGradient,
                        borderRadius: BorderRadius.circular(22),
                        border: Border.all(color: AppTheme.primary.withValues(alpha: 0.35), width: 1.2),
                        boxShadow: [
                          BoxShadow(
                            color: AppTheme.primaryGlow.withValues(alpha: 0.15),
                            blurRadius: 24,
                            offset: const Offset(0, 8),
                          ),
                        ],
                      ),
                      child: Row(
                        children: [
                          Expanded(
                            child: Column(
                              crossAxisAlignment: CrossAxisAlignment.start,
                              children: [
                                const Text(
                                  'Resurrect Presence',
                                  style: TextStyle(
                                    color: AppTheme.textPrimary,
                                    fontSize: 18,
                                    fontWeight: FontWeight.bold,
                                  ),
                                ),
                                const SizedBox(height: 6),
                                const Text(
                                  'Upload an authorized voice sample and design their conversational soul.',
                                  style: TextStyle(
                                    color: AppTheme.textSecondary,
                                    fontSize: 13,
                                    height: 1.35,
                                  ),
                                ),
                                const SizedBox(height: 16),
                                ElevatedButton.icon(
                                  onPressed: () => Navigator.pushNamed(context, AppRouter.createRevival),
                                  icon: const Icon(Icons.add_rounded, size: 20),
                                  label: const Text('Create New Revival'),
                                  style: ElevatedButton.styleFrom(
                                    padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 12),
                                    shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(14)),
                                  ),
                                ),
                              ],
                            ),
                          ),
                          const SizedBox(width: 14),
                          Container(
                            width: 60,
                            height: 60,
                            decoration: BoxDecoration(
                              shape: BoxShape.circle,
                              gradient: AppTheme.voiceGradient,
                            ),
                            child: const Icon(Icons.mic_external_on_rounded, color: Colors.white, size: 30),
                          ),
                        ],
                      ),
                    ),
                    const SizedBox(height: 32),

                    // Section Title
                    Row(
                      mainAxisAlignment: MainAxisAlignment.spaceBetween,
                      children: [
                        const Text(
                          'Your Revivals',
                          style: TextStyle(
                            color: AppTheme.textPrimary,
                            fontSize: 18,
                            fontWeight: FontWeight.bold,
                          ),
                        ),
                        if (revivals.isNotEmpty)
                          Text(
                            '${revivals.length} Total',
                            style: const TextStyle(color: AppTheme.textMuted, fontSize: 13),
                          ),
                      ],
                    ),
                  ],
                ),
              ),
            ),

            // Revival List
            if (isLoading) ...[
              const SliverFillRemaining(
                child: Center(
                  child: CircularProgressIndicator(color: AppTheme.accent),
                ),
              ),
            ] else if (revivals.isEmpty) ...[
              SliverFillRemaining(
                hasScrollBody: false,
                child: Padding(
                  padding: const EdgeInsets.symmetric(horizontal: 40),
                  child: Column(
                    mainAxisAlignment: MainAxisAlignment.center,
                    children: [
                      Icon(Icons.record_voice_over_outlined, color: AppTheme.textMuted.withValues(alpha: 0.4), size: 68),
                      const SizedBox(height: 16),
                      const Text(
                        'No Revivals Created Yet',
                        style: TextStyle(color: AppTheme.textPrimary, fontSize: 18, fontWeight: FontWeight.w600),
                      ),
                      const SizedBox(height: 8),
                      const Text(
                        'Start by uploading a reference voice to create your first voice-first character.',
                        style: TextStyle(color: AppTheme.textSecondary, fontSize: 13),
                        textAlign: TextAlign.center,
                      ),
                      const SizedBox(height: 24),
                      ElevatedButton(
                        onPressed: () => Navigator.pushNamed(context, AppRouter.createRevival),
                        child: const Text('Create First Revival'),
                      ),
                    ],
                  ),
                ),
              ),
            ] else ...[
              SliverPadding(
                padding: const EdgeInsets.symmetric(horizontal: 22),
                sliver: SliverList(
                  delegate: SliverChildBuilderDelegate(
                    (context, index) {
                      final rev = revivals[index];
                      return RevivalCardWidget(
                        revival: rev,
                        onTap: () {
                          revivalProv.selectRevival(rev);
                          Navigator.pushNamed(context, AppRouter.characterSetup);
                        },
                        onStartConversation: () async {
                          revivalProv.selectRevival(rev);
                          final convProv = context.read<ConversationProvider>();
                          await convProv.startNewConversation(rev.id, title: 'Chat with ${rev.name}');
                          if (context.mounted) {
                            Navigator.pushNamed(context, AppRouter.conversation);
                          }
                        },
                      );
                    },
                    childCount: revivals.length,
                  ),
                ),
              ),
            ],
          ],
        ),
      ),
    );
  }
}
