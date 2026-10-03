part of '../../../imports.dart';

class ProfileScaffold extends StatelessWidget {
  const ProfileScaffold({
    super.key,
    required this.workspace,
    required this.body,
    this.showBackButton = false,
  });

  final AppWorkspace workspace;
  final Widget body;
  final bool showBackButton;

  @override
  Widget build(BuildContext context) {
    Localizations.localeOf(context);
    return AppScaffold(
      title: LocaleKeys.profile,
      showBackButton: showBackButton,
      actions: [
        IconButton(
          tooltip: LocaleKeys.profileHelpCenter,
          onPressed: () => Go.to(SupportScreen(workspace: workspace)),
          icon: const Icon(Icons.support_agent_rounded),
        ),
        IconButton(
          tooltip: LocaleKeys.profileSettingsTitle,
          onPressed: () => Go.to(ProfileSettingsScreen(workspace: workspace)),
          icon: const Icon(Icons.settings_outlined),
        ),
      ],
      body: SafeArea(child: body),
    );
  }
}
