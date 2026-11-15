from pathlib import Path
p=Path('/Users/demo23home/code/sukoon/sokoun/apps/sokoun_app/lib/features/shared/profile/presentation/widgets/settings/security_sessions_body.dart')
s=p.read_text()
a=s.index('  @override\n  Widget build')
s=s[:a]+'''  @override
  Widget build(BuildContext context) {
    final palette = SokounPalette.of(context);
    return SingleChildScrollView(
      padding: const EdgeInsets.fromLTRB(20, 12, 20, 24),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        spacing: 16,
        children: [
          SokounPageIntro(
            title: LocaleKeys.uiSessionsTitle,
            description: LocaleKeys.securitySessionsHelp,
            showTitle: false,
            compact: true,
          ),
          ProfileSurfaceCard(
            padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 4),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.stretch,
              children: [
                TextButton.icon(
                  style: TextButton.styleFrom(alignment: AlignmentDirectional.centerStart, minimumSize: const Size(0, 48)),
                  icon: const Icon(Icons.history_rounded, size: 20),
                  onPressed: () => Go.to(const NotificationsScreen(scope: NotificationScope.account)),
                  label: AppText(LocaleKeys.accountSecurityEvents),
                ),
                Divider(height: 1, color: palette.line),
                TextButton.icon(
                  style: TextButton.styleFrom(alignment: AlignmentDirectional.centerStart, minimumSize: const Size(0, 48)),
                  icon: const Icon(Icons.support_agent_rounded, size: 20),
                  onPressed: () => Go.to(SupportTicketsScreen(workspace: workspace, scope: SupportScope.account)),
                  label: AppText(LocaleKeys.supportAccountTickets),
                ),
              ],
            ),
          ),
          if (value.frozen) AppText(LocaleKeys.securityActionsRestricted),
          if (value.items.isEmpty)
            PremiumEmptyState(title: LocaleKeys.securitySessionsTitle, description: LocaleKeys.securitySessionsEmpty),
          for (final session in value.items)
            _SecuritySessionCard(session: session, write: write, revokeSession: revokeSession),
          BlocBuilder<SecurityRevocationCubit, AsyncState<SecurityRevocationState>>(
            bloc: write,
            builder: (context, state) => ProfileSurfaceCard(
              padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 4),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.stretch,
                children: [
                  if (state.isError)
                    Padding(padding: const EdgeInsets.all(8), child: AppText(state.msg ?? LocaleKeys.exceptionError)),
                  if (revokeOthers != null) ...[
                    TextButton.icon(
                      style: TextButton.styleFrom(alignment: AlignmentDirectional.centerStart, minimumSize: const Size(0, 48), foregroundColor: palette.error),
                      icon: const Icon(Icons.devices_outlined, size: 20),
                      onPressed: state.isLoading ? null : revokeOthers,
                      label: AppText(LocaleKeys.securityEndOthers),
                    ),
                    Divider(height: 1, color: palette.line),
                  ],
                  TextButton.icon(
                    style: TextButton.styleFrom(alignment: AlignmentDirectional.centerStart, minimumSize: const Size(0, 48), foregroundColor: palette.error),
                    icon: const Icon(Icons.logout_rounded, size: 20),
                    onPressed: state.isLoading ? null : revoke,
                    label: AppText(LocaleKeys.securityEndAll),
                  ),
                ],
              ),
            ),
          ),
        ],
      ),
    );
  }
}

class _SecuritySessionCard extends StatelessWidget {
  const _SecuritySessionCard({required this.session, required this.write, this.revokeSession});
  final SecuritySession session;
  final SecurityRevocationCubit write;
  final Future<void> Function(SecuritySession)? revokeSession;

  @override
  Widget build(BuildContext context) {
    final palette = SokounPalette.of(context);
    final theme = Theme.of(context);
    return ProfileSurfaceCard(
      padding: const EdgeInsets.all(16),
      child: Column(
        mainAxisSize: MainAxisSize.min,
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          Row(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Container(
                padding: const EdgeInsets.all(10),
                decoration: BoxDecoration(color: palette.chip, borderRadius: BorderRadius.circular(12)),
                child: Icon(Icons.devices_outlined, color: palette.accent, size: 22),
              ),
              const SizedBox(width: 12),
              Expanded(child: Column(
                mainAxisSize: MainAxisSize.min,
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  AppText(session.model.isEmpty ? LocaleKeys.securityUnknownDevice : session.model,
                    style: theme.textTheme.titleSmall?.copyWith(color: palette.text, height: 1.5)),
                  if (session.platform.isNotEmpty || session.os.isNotEmpty || session.appVersion.isNotEmpty)
                    AppText([
                      [session.platform, session.os].where((v) => v.isNotEmpty).join(' '),
                      session.appVersion,
                    ].where((v) => v.isNotEmpty).join(' · '),
                      style: theme.textTheme.bodySmall?.copyWith(color: palette.muted, height: 1.5)),
                  if (session.current) ...[
                    const SizedBox(height: 6),
                    AppText(LocaleKeys.securityCurrentSession,
                      style: theme.textTheme.bodySmall?.copyWith(color: palette.accent, height: 1.5)),
                  ],
                ],
              )),
            ],
          ),
          const SizedBox(height: 12),
          Divider(height: 1, color: palette.line),
          const SizedBox(height: 12),
          if (session.lastSeen.isNotEmpty)
            RentalInstantField(label: LocaleKeys.securityLastActive, value: session.lastSeen),
          const SizedBox(height: 8),
          RentalInstantField(label: LocaleKeys.securitySessionCreated, value: session.createdAt),
          if (revokeSession != null) ...[
            const SizedBox(height: 8),
            BlocBuilder<SecurityRevocationCubit, AsyncState<SecurityRevocationState>>(
              bloc: write,
              builder: (_, state) => Align(
                alignment: AlignmentDirectional.centerStart,
                child: TextButton.icon(
                  style: TextButton.styleFrom(foregroundColor: palette.error, minimumSize: const Size(0, 48)),
                  icon: const Icon(Icons.logout_rounded, size: 18),
                  onPressed: state.isLoading ? null : () => revokeSession!(session),
                  label: AppText(LocaleKeys.securityEndSession),
                ),
              ),
            ),
          ],
        ],
      ),
    );
  }
}
'''
p.write_text(s)
