part of '../../imports.dart';

class ProfileSettingsScreen extends StatelessWidget {
  const ProfileSettingsScreen({
    super.key,
    this.workspace = AppWorkspace.tenant,
  });
  final AppWorkspace workspace;
  @override
  Widget build(BuildContext context) {
    Localizations.localeOf(context);
    return AppScaffold(
      title: LocaleKeys.profileSettingsTitle,
      body: SafeArea(child: ProfileSettingsContentView(workspace: workspace)),
    );
  }
}
