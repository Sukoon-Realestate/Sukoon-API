part of '../../imports.dart';

class ProfileEditScreen extends StatelessWidget {
  const ProfileEditScreen({
    super.key,
    required this.initialValue,
    required this.workspace,
  });

  final UserModel initialValue;
  final AppWorkspace workspace;

  @override
  Widget build(BuildContext context) =>
      ProfileEditView(initialValue: initialValue, workspace: workspace);
}
