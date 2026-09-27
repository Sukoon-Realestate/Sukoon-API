part of '../../imports.dart';

class OwnerEditProfileScreen extends StatelessWidget {
  const OwnerEditProfileScreen({super.key, required this.initialValue});

  final UserModel initialValue;

  @override
  Widget build(BuildContext context) {
    return ProfileEditView(
      initialValue: initialValue,
      workspace: AppWorkspace.owner,
    );
  }
}
