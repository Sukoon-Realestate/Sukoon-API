part of '../../../imports.dart';

class TenantProfileContentView extends StatelessWidget {
  const TenantProfileContentView({
    super.key,
    required this.profile,
    required this.onEditPressed,
  });

  final AccountContent profile;
  final VoidCallback onEditPressed;

  @override
  Widget build(BuildContext context) {
    return ProfileContentView(
      workspace: AppWorkspace.tenant,
      header: TenantProfileHeaderCard(
        profile: profile,
        onEditPressed: onEditPressed,
      ),
      accountDetails: profile.accountDetails,
      isVerified: profile.user.isVerified,
      verificationSubtitle: profile.menuItems.verification.subtitle,
      activity: TenantProfileActions(menuItems: profile.menuItems),
    );
  }
}
