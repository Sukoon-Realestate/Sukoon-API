part of '../../imports.dart';

class ChangePasswordScreen extends StatelessWidget {
  const ChangePasswordScreen({super.key});
  @override
  Widget build(BuildContext context) => AppScaffold(
    title: LocaleKeys.settingsChangePassword,
    contentWidth: SokounContentWidth.form,
    body: const ChangePasswordForm(),
  );
}
