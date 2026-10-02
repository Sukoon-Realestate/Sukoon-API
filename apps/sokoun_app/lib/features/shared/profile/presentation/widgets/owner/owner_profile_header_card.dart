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
            spacing: 14.w,
            children: [
              ProfileAvatar(
                name: userName,
                avatarUrl: owner.avatar,
                accentColor: AppColors.sokoonGold,
                backgroundColor: AppColors.goldPale,
                badgeIcon: owner.isVerified ? Icons.check_rounded : null,
              ),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Row(
                      spacing: 8.w,
                      children: [
                        Flexible(
                          child: AppText(
                            userName,
                            style: AppTextStyles.bold.copyWith(
                              color: AppColors.sokoonNavy,
                              fontSize: 18.sp,
                            ),
                            maxLines: 1,
                            overflow: TextOverflow.ellipsis,
                          ),
                        ),
                        ProfileVerifiedBadge(
                          text: owner.roleBadge.isNotEmpty
                              ? owner.roleBadge
                              : owner.isVerified
                              ? LocaleKeys.profileVerifiedOwner
                              : LocaleKeys.workspaceOwner,
                          isVerified: owner.isVerified,
                        ),
                      ],
                    ),
                    5.szH,
                    Row(
                      spacing: 4.w,
                      children: [
                        Icon(
                          Icons.star_rounded,
                          color: AppColors.amber,
                          size: 14.r,
                        ),
                        Flexible(
                          child: AppText(
                            owner.ratingLabel.isNotEmpty
                                ? owner.ratingLabel
                                : LocaleKeys.profileRatingSummaryLabel
                                      .replaceAll(
                                        '{rating}',
                                        owner.averageRating.toStringAsFixed(1),
                                      )
                                      .replaceAll(
                                        '{count}',
                                        '${owner.reviewsCount}',
                                      ),
                            style: AppTextStyles.regular12.copyWith(
                              color: AppColors.sokoonGray,
                              fontSize: 12.sp,
                              height: 1.45,
                            ),
                          ),
                        ),
                      ],
                    ),
                    2.szH,
                    AppText(
                      owner.memberSinceLabel.isNotEmpty
                          ? owner.memberSinceLabel
                          : LocaleKeys.notSetYet,
                      style: AppTextStyles.regular12.copyWith(
                        color: AppColors.sokoonGray,
                        fontSize: 12.sp,
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
