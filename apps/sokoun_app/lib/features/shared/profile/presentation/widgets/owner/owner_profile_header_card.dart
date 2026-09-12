part of '../../../imports.dart';

class OwnerProfileHeaderCard extends StatelessWidget {
  const OwnerProfileHeaderCard({super.key, required this.profile});

  final OwnerProfileContent profile;

  @override
  Widget build(BuildContext context) {
    final OwnerProfileIdentityContent owner = profile.owner;
    final OwnerProfileStatsContent stats = profile.stats;
    final String userName = owner.fullName.trim().isEmpty
        ? LocaleKeys.profileFallbackName
        : owner.fullName;

    return ProfileSurfaceCard(
      child: Column(
        children: [
          Row(
            children: [
              ProfileAvatar(
                name: userName,
                avatarUrl: owner.avatar,
                accentColor: AppColors.sokoonGold,
                backgroundColor: AppColors.goldPale,
                badgeIcon: Icons.check_rounded,
              ),
              14.szW,
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Row(
                      children: [
                        Flexible(
                          child: AppText(
                            userName,
                            color: AppColors.sokoonNavy,
                            fontSize: 18.sp,
                            fontWeight: FontWeight.w900,
                            maxLines: 1,
                            overflow: TextOverflow.ellipsis,
                          ),
                        ),
                        8.szW,
                        ProfileVerifiedBadge(
                          text: owner.roleBadge.isNotEmpty
                              ? owner.roleBadge
                              : LocaleKeys.profileVerifiedOwner,
                          isVerified: owner.isVerified,
                        ),
                      ],
                    ),
                    5.szH,
                    Row(
                      children: [
                        Icon(
                          Icons.star_rounded,
                          color: AppColors.amber,
                          size: 14.r,
                        ),
                        4.szW,
                        AppText(
                          owner.ratingLabel.isNotEmpty
                              ? owner.ratingLabel
                              : LocaleKeys.profileOwnerRatingSummary,
                          color: AppColors.sokoonGray,
                          fontSize: 12.sp,
                        ),
                      ],
                    ),
                    2.szH,
                    AppText(
                      owner.memberSinceLabel.isNotEmpty
                          ? owner.memberSinceLabel
                          : LocaleKeys.profileOwnerMemberSince,
                      color: AppColors.sokoonGray,
                      fontSize: 12.sp,
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
                value: '${stats.propertiesCount}',
                label: stats.propertiesLabel.isNotEmpty
                    ? stats.propertiesLabel
                    : LocaleKeys.profileProperties,
              ),
              ProfileStat(
                value: '${stats.reviewsCount}',
                label: stats.reviewsLabel.isNotEmpty
                    ? stats.reviewsLabel
                    : LocaleKeys.profileReviews,
              ),
              ProfileStat(
                value: stats.displayAcceptanceRate,
                label: stats.acceptanceLabel.isNotEmpty
                    ? stats.acceptanceLabel
                    : LocaleKeys.profileAcceptance,
              ),
            ],
          ),
        ],
      ),
    );
  }
}
