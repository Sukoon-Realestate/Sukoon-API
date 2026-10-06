part of '../../../imports.dart';

class TenantProfileHeaderCard extends StatelessWidget {
  const TenantProfileHeaderCard({
    super.key,
    required this.profile,
    required this.onEditPressed,
  });

  final AccountContent profile;
  final VoidCallback onEditPressed;

  @override
  Widget build(BuildContext context) {
    final WorkspaceCounts? counts = context
        .select<UnreadCountsCubit?, WorkspaceCounts?>(
          (cubit) =>
              cubit?.state.isSuccess == true ? cubit?.state.data.tenant : null,
        );
    final AccountUserContent user = profile.user;
    final String membership = [
      user.roleLabel,
      user.memberSinceLabel,
    ].where((value) => value.isNotEmpty).join(' · ');
    return ProfileHeaderCard(
      workspace: AppWorkspace.tenant,
      name: user.fullName,
      avatarUrl: user.avatar,
      isVerified: user.isVerified,
      badgeText: user.verificationBadge.isNotEmpty
          ? user.verificationBadge
          : LocaleKeys.verified,
      membership: membership.isNotEmpty
          ? membership
          : LocaleKeys.workspaceTenant,
      onEditPressed: onEditPressed,
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
    );
  }
}
