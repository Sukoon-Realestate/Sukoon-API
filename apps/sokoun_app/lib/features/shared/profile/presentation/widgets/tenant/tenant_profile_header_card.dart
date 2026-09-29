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
            children: [
              ProfileAvatar(
                name: userName,
                avatarUrl: user.avatar,
                accentColor: AppColors.sokoonTeal,
                backgroundColor: AppColors.mintLight,
                badgeIcon: Icons.edit_outlined,
                onBadgePressed: onEditPressed,
              ),
              14.szW,
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Wrap(
                      spacing: 8.w,
                      runSpacing: 4.h,
                      children: [
                        AppText(
                          userName,
                          color: AppColors.sokoonNavy,
                          fontSize: 18.sp,
                          fontWeight: FontWeight.w700,
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
                    4.szH,
                    AppText(
                      membership.isNotEmpty
                          ? membership
                          : LocaleKeys.profileTenantMemberSince,
                      color: AppColors.sokoonGray,
                      fontSize: 13.sp,
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
                value: '${profile.stats.savedCount}',
                label: LocaleKeys.profileSaved,
              ),
              ProfileStat(
                value: '${profile.stats.visitsCount}',
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
