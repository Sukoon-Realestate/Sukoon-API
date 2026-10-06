part of '../../../imports.dart';

class ProfileVerificationTile extends StatelessWidget {
  const ProfileVerificationTile({
    super.key,
    required this.workspace,
    required this.isVerified,
    this.subtitle,
  });

  final AppWorkspace workspace;
  final bool isVerified;
  final String? subtitle;

  @override
  Widget build(BuildContext context) => ProfileSurfaceCard(
    child: ProfileMenuTile(
      icon: Icons.verified_user_outlined,
      label: LocaleKeys.profileIdentityVerification,
      subtitle: subtitle?.trim().isNotEmpty == true
          ? subtitle
          : isVerified
          ? LocaleKeys.verified
          : LocaleKeys.ownerHomeUnverified,
      iconColor: workspace.isOwner
          ? AppColors.sokoonGold
          : context.appColor(AppColors.sokoonTeal),
      iconBackgroundColor: workspace.isOwner
          ? context.appColor(AppColors.goldPale, surface: true)
          : context.appColor(AppColors.mintLight, surface: true),
      onTap: () => Go.to(ProfileVerificationScreen(workspace: workspace)),
    ),
  );
}
