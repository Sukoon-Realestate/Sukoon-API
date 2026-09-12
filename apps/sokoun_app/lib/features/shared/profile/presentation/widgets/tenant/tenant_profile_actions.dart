part of '../../../imports.dart';

class TenantProfileActions extends StatelessWidget {
  const TenantProfileActions({super.key, required this.menuItems});

  final TenantProfileMenuItemsContent menuItems;

  @override
  Widget build(BuildContext context) {
    return Column(
      children: [
        ProfileSurfaceCard(
          padding: EdgeInsets.symmetric(horizontal: 16.w, vertical: 2.h),
          child: ProfileMenuTile(
            icon: Icons.calendar_month_outlined,
            label: menuItems.visitRequests.title.isNotEmpty
                ? menuItems.visitRequests.title
                : LocaleKeys.profileVisitRequests,
            subtitle: menuItems.visitRequests.subtitle.isNotEmpty
                ? menuItems.visitRequests.subtitle
                : LocaleKeys.profileVisitRequestsCount,
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
            label: menuItems.contracts.title.isNotEmpty
                ? menuItems.contracts.title
                : LocaleKeys.profileContracts,
            subtitle: menuItems.contracts.subtitle.isNotEmpty
                ? menuItems.contracts.subtitle
                : LocaleKeys.profileActiveContractCount,
            iconColor: AppColors.blue,
            iconBackgroundColor: AppColors.bluePale,
          ),
        ),
        8.szH,
        ProfileSurfaceCard(
          padding: EdgeInsets.symmetric(horizontal: 16.w, vertical: 2.h),
          child: ProfileMenuTile(
            icon: Icons.star_outline_rounded,
            label: menuItems.reviews.title.isNotEmpty
                ? menuItems.reviews.title
                : LocaleKeys.profileMyReviews,
            subtitle: menuItems.reviews.subtitle.isNotEmpty
                ? menuItems.reviews.subtitle
                : LocaleKeys.profileReviewsCount,
            iconColor: AppColors.amber,
            iconBackgroundColor: AppColors.orangePale,
          ),
        ),
        8.szH,
        ProfileSurfaceCard(
          padding: EdgeInsets.symmetric(horizontal: 16.w, vertical: 2.h),
          child: ProfileMenuTile(
            icon: Icons.shield_outlined,
            label: menuItems.verification.title.isNotEmpty
                ? menuItems.verification.title
                : LocaleKeys.profileVerificationAndPrivacy,
            subtitle: menuItems.verification.subtitle.isNotEmpty
                ? menuItems.verification.subtitle
                : LocaleKeys.verified,
            iconColor: menuItems.verification.isVerified
                ? AppColors.green
                : AppColors.sokoonGray,
            iconBackgroundColor: menuItems.verification.isVerified
                ? AppColors.greenPale
                : AppColors.grayBackground,
            onTap: () => Go.to(
              menuItems.verification.isVerified
                  ? const KycApprovedScreen()
                  : const KycIntroScreen(),
            ),
          ),
        ),
      ],
    );
  }
}
