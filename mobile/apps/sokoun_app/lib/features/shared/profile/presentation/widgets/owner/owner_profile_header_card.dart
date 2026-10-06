part of '../../../imports.dart';

class OwnerProfileHeaderCard extends StatelessWidget {
  const OwnerProfileHeaderCard({
    super.key,
    required this.profile,
    required this.onEditPressed,
  });

  final OwnerProfileContent profile;
  final VoidCallback onEditPressed;

  @override
  Widget build(BuildContext context) {
    final OwnerProfileIdentityContent owner = profile.owner;
    final OwnerProfileStatsContent stats = profile.stats;
    return ProfileHeaderCard(
      workspace: AppWorkspace.owner,
      name: owner.fullName,
      avatarUrl: owner.avatar,
      isVerified: owner.isVerified,
      badgeText: owner.roleBadge.isNotEmpty
          ? owner.roleBadge
          : LocaleKeys.profileVerifiedOwner,
      membership: owner.memberSinceLabel.isNotEmpty
          ? owner.memberSinceLabel
          : LocaleKeys.workspaceOwner,
      rating: OwnerProfileRating(
        rating: owner.averageRating,
        reviewsCount: owner.reviewsCount,
        label: owner.ratingLabel,
      ),
      onEditPressed: onEditPressed,
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
    );
  }
}
