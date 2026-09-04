part of '../../../imports.dart';

class TenantProfileHeaderCard extends StatelessWidget {
  const TenantProfileHeaderCard({
    super.key,
    required this.user,
    required this.onEditPressed,
  });

  final UserModel user;
  final VoidCallback onEditPressed;

  @override
  Widget build(BuildContext context) {
    final String userName = user.name.trim().isEmpty
        ? LocaleKeys.profileFallbackName
        : user.name;

    return ProfileSurfaceCard(
      child: Column(
        children: [
          Row(
            children: [
              ProfileAvatar(
                name: userName,
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
                        const ProfileVerifiedBadge(),
                      ],
                    ),
                    4.szH,
                    AppText(
                      LocaleKeys.profileTenantMemberSince,
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
              ProfileStat(value: '12', label: LocaleKeys.profileSaved),
              ProfileStat(value: '4', label: LocaleKeys.profileVisits),
              ProfileStat(value: '2', label: LocaleKeys.profileReviews),
            ],
          ),
        ],
      ),
    );
  }
}
