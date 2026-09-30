part of '../../../imports.dart';

class TenantProfileHeaderCard extends StatelessWidget {
  const TenantProfileHeaderCard({
    super.key,
    required this.profile,
    required this.onEditPressed,
  });

  final TenantProfileContent profile;
  final VoidCallback onEditPressed;

  @override
  Widget build(BuildContext context) {
    final WorkspaceCounts? counts = context
        .select<WorkspaceCountsCubit?, WorkspaceCounts?>(
          (cubit) => cubit?.state.isSuccess == true ? cubit?.state.data : null,
        );
    final TenantProfileUserContent user = profile.user;
    final String userName = user.fullName.trim().isEmpty
        ? LocaleKeys.profileFallbackName
        : user.fullName;
    final String membership = [
      user.roleLabel,
      user.memberSinceLabel,
    ].where((value) => value.isNotEmpty).join(' · ');

    return ProfileSurfaceCard(
      child: Column(
        children: [
          Row(
            spacing: 14.w,
            children: [
              ProfileAvatar(
                name: userName,
                avatarUrl: user.avatar,
                accentColor: AppColors.sokoonTeal,
                backgroundColor: AppColors.mintLight,
                badgeIcon: Icons.edit_outlined,
                onBadgePressed: onEditPressed,
              ),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  spacing: 4.h,
                  children: [
                    Wrap(
                      spacing: 8.w,
                      runSpacing: 4.h,
                      children: [
                        AppText(
                          userName,
                          style: AppTextStyles.bold.copyWith(
                            color: AppColors.sokoonNavy,
                            fontSize: 18.sp,
                          ),
                          maxLines: 1,
                          overflow: TextOverflow.ellipsis,
                        ),
                        ProfileVerifiedBadge(
                          text: user.verificationBadge.isNotEmpty
                              ? user.verificationBadge
                              : LocaleKeys.verified,
                          isVerified: user.isVerified,
                        ),
                      ],
                    ),
                    AppText(
                      membership.isNotEmpty
                          ? membership
                          : LocaleKeys.profileTenantMemberSince,
                      style: AppTextStyles.regular13.copyWith(
                        color: AppColors.sokoonGray,
                        fontSize: 13.sp,
                        height: 1.45,
                      ),
                    ),
                  ],
                ),
              ),
            ],
          ),
          14.szH,
          const Divider(height: 1, color: AppColors.sokoonBorder),
          12.szH,
          ProfileStatGrid(
            stats: [
              ProfileStat(
                value: '${counts?.favorites ?? profile.stats.savedCount}',
                label: LocaleKeys.profileSaved,
              ),
              ProfileStat(
                value: '${counts?.visits ?? profile.stats.visitsCount}',
                label: LocaleKeys.profileVisits,
              ),
              ProfileStat(
                value: '${profile.stats.reviewsCount}',
                label: LocaleKeys.profileReviews,
              ),
            ],
          ),
        ],
      ),
    );
  }
}
