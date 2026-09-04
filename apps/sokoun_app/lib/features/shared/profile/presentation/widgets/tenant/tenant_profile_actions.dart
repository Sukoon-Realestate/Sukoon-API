part of '../../../imports.dart';

class TenantProfileActions extends StatelessWidget {
  const TenantProfileActions({super.key});

  @override
  Widget build(BuildContext context) {
    return Column(
      children: [
        ProfileSurfaceCard(
          padding: EdgeInsets.symmetric(horizontal: 16.w, vertical: 2.h),
          child: ProfileMenuTile(
            icon: Icons.calendar_month_outlined,
            label: LocaleKeys.profileVisitRequests,
            subtitle: LocaleKeys.profileVisitRequestsCount,
            iconColor: AppColors.sokoonTeal,
            iconBackgroundColor: AppColors.mintLight,
            onTap: () => Go.to(const TenantVisitsScreen()),
          ),
        ),
        8.szH,
        ProfileSurfaceCard(
          padding: EdgeInsets.symmetric(horizontal: 16.w, vertical: 2.h),
          child: ProfileMenuTile(
            icon: Icons.description_outlined,
            label: LocaleKeys.profileContracts,
            subtitle: LocaleKeys.profileActiveContractCount,
            iconColor: AppColors.blue,
            iconBackgroundColor: AppColors.bluePale,
          ),
        ),
        8.szH,
        ProfileSurfaceCard(
          padding: EdgeInsets.symmetric(horizontal: 16.w, vertical: 2.h),
          child: ProfileMenuTile(
            icon: Icons.star_outline_rounded,
            label: LocaleKeys.profileMyReviews,
            subtitle: LocaleKeys.profileReviewsCount,
            iconColor: AppColors.amber,
            iconBackgroundColor: AppColors.orangePale,
          ),
        ),
        8.szH,
        ProfileSurfaceCard(
          padding: EdgeInsets.symmetric(horizontal: 16.w, vertical: 2.h),
          child: ProfileMenuTile(
            icon: Icons.shield_outlined,
            label: LocaleKeys.profileVerificationAndPrivacy,
            subtitle: LocaleKeys.verified,
            iconColor: AppColors.green,
            iconBackgroundColor: AppColors.greenPale,
            onTap: () => Go.to(const KycApprovedScreen()),
          ),
        ),
      ],
    );
  }
}
