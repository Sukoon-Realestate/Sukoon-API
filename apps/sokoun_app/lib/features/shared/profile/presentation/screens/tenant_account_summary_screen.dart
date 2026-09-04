part of '../../imports.dart';

class TenantAccountSummaryScreen extends StatelessWidget {
  const TenantAccountSummaryScreen({super.key, required this.user});

  final UserModel user;

  @override
  Widget build(BuildContext context) {
    return Directionality(
      textDirection: TextDirection.rtl,
      child: Scaffold(
        key: const ValueKey('T-SUMMARY-01'),
        backgroundColor: AppColors.scaffoldBackground,
        body: SafeArea(
          child: Column(
            children: [
              ProfileScreenHeader(
                title: LocaleKeys.profileSummaryTitle,
                showBackButton: true,
              ),
              Expanded(
                child: ListView(
                  padding: EdgeInsets.all(20.r),
                  children: [
                    TenantSummaryHeaderCard(user: user),
                    18.szH,
                    ProfileVerificationBanner(
                      title: LocaleKeys.profileIdentityVerified,
                      description:
                          LocaleKeys.profileIdentityVerifiedDescription,
                    ),
                    18.szH,
                    ProfileStatGrid(
                      withCards: true,
                      valueColor: AppColors.sokoonTeal,
                      stats: [
                        ProfileStat(
                          value: '12',
                          label: LocaleKeys.profileSavedProperties,
                        ),
                        ProfileStat(
                          value: '4',
                          label: LocaleKeys.profileCompletedVisits,
                        ),
                        ProfileStat(
                          value: '3',
                          label: LocaleKeys.profileActiveChats,
                        ),
                      ],
                    ),
                    18.szH,
                    ProfileSurfaceCard(
                      padding: EdgeInsets.symmetric(
                        horizontal: 16.w,
                        vertical: 2.h,
                      ),
                      child: Column(
                        children: [
                          ProfileMenuTile(
                            icon: Icons.favorite_border_rounded,
                            label: LocaleKeys.profileSavedProperties,
                            value: '12',
                            iconColor: AppColors.sokoonTeal,
                            iconBackgroundColor: AppColors.mintLight,
                            showDivider: true,
                          ),
                          ProfileMenuTile(
                            icon: Icons.calendar_month_outlined,
                            label: LocaleKeys.profileVisitHistory,
                            value: '4',
                            iconColor: AppColors.sokoonTeal,
                            iconBackgroundColor: AppColors.mintLight,
                            onTap: () => Go.to(const TenantVisitsScreen()),
                            showDivider: true,
                          ),
                          ProfileMenuTile(
                            icon: Icons.shield_outlined,
                            label: LocaleKeys.profileIdentityVerification,
                            value: LocaleKeys.profileCompleteStatus,
                            iconColor: AppColors.sokoonTeal,
                            iconBackgroundColor: AppColors.mintLight,
                            onTap: () => Go.to(const KycApprovedScreen()),
                          ),
                        ],
                      ),
                    ),
                  ],
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }
}
