part of '../../../imports.dart';

class ProfileHeaderCard extends StatelessWidget {
  const ProfileHeaderCard({
    super.key,
    required this.workspace,
    required this.name,
    required this.avatarUrl,
    required this.isVerified,
    required this.badgeText,
    required this.membership,
    required this.stats,
    required this.onEditPressed,
    this.rating,
  });

  final AppWorkspace workspace;
  final String name;
  final String? avatarUrl;
  final bool isVerified;
  final String badgeText;
  final String membership;
  final List<ProfileStat> stats;
  final VoidCallback onEditPressed;
  final Widget? rating;

  @override
  Widget build(BuildContext context) {
    final String displayName = name.trim().isEmpty
        ? LocaleKeys.profileFallbackName
        : name;
    return ProfileSurfaceCard(
      child: Column(
        children: [
          ProfileIdentityHeader(
            avatar: ProfileAvatar(
              name: displayName,
              avatarUrl: avatarUrl,
              accentColor: workspace.isOwner
                  ? AppColors.sokoonGold
                  : AppColors.sokoonTeal,
              backgroundColor: workspace.isOwner
                  ? AppColors.goldPale
                  : AppColors.mintLight,
            ),
            details: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              spacing: 4.h,
              children: [
                Wrap(
                  spacing: 8.w,
                  runSpacing: 4.h,
                  crossAxisAlignment: WrapCrossAlignment.center,
                  children: [
                    AppText(
                      displayName,
                      style: AppTextStyles.bold.copyWith(
                        color: AppColors.sokoonNavy,
                        fontSize: 18.sp,
                      ),
                    ),
                    ProfileVerifiedBadge(
                      text: badgeText,
                      isVerified: isVerified,
                    ),
                  ],
                ),
                if (rating != null) rating!,
                AppText(
                  membership,
                  style: AppTextStyles.regular13.copyWith(
                    color: AppColors.sokoonGray,
                    height: 1.45,
                  ),
                ),
              ],
            ),
          ),
          14.szH,
          const Divider(height: 1, color: AppColors.sokoonBorder),
          12.szH,
          ProfileStatGrid(stats: stats),
          12.szH,
          SizedBox(
            width: double.infinity,
            child: OutlinedButton.icon(
              onPressed: onEditPressed,
              icon: const Icon(Icons.edit_outlined),
              label: Text(LocaleKeys.profileEditAction),
            ),
          ),
        ],
      ),
    );
  }
}
