part of '../../../imports.dart';

class OwnerProfileHeaderCard extends StatelessWidget {
  const OwnerProfileHeaderCard({super.key, required this.user});

  final UserModel user;

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
                          text: LocaleKeys.profileVerifiedOwner,
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
                          LocaleKeys.profileOwnerRatingSummary,
                          color: AppColors.sokoonGray,
                          fontSize: 12.sp,
                        ),
                      ],
                    ),
                    2.szH,
                    AppText(
                      LocaleKeys.profileOwnerMemberSince,
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
              ProfileStat(value: '3', label: LocaleKeys.profileProperties),
              ProfileStat(value: '42', label: LocaleKeys.profileReviews),
              ProfileStat(value: '96%', label: LocaleKeys.profileAcceptance),
            ],
          ),
        ],
      ),
    );
  }
}
