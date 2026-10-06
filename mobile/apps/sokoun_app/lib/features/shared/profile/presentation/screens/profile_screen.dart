part of '../../imports.dart';

/// The account entry point shared by both navigation workspaces.
class ProfileScreen extends StatelessWidget {
  const ProfileScreen({
    super.key,
    required this.workspace,
    this.user,
    this.showBackButton = false,
  });

  final AppWorkspace workspace;
  final UserModel? user;
  final bool showBackButton;

  @override
  Widget build(BuildContext context) => workspace.isOwner
      ? OwnerProfileScreen(user: user, showBackButton: showBackButton)
      : TenantProfileScreen(user: user, showBackButton: showBackButton);
}
