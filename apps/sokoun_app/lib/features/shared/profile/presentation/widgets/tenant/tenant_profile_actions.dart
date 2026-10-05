part of '../../../imports.dart';

class TenantProfileActions extends StatelessWidget {
  const TenantProfileActions({super.key, required this.menuItems});

  final AccountMenuItemsContent menuItems;

  @override
  Widget build(BuildContext context) {
    return Column(
      spacing: 8.h,
      children: [
        ProfileSurfaceCard(
          padding: EdgeInsets.symmetric(horizontal: 16.w, vertical: 2.h),
          child: ProfileMenuTile(
            icon: Icons.description_outlined,
            label: menuItems.contracts.title.isNotEmpty
                ? menuItems.contracts.title
                : LocaleKeys.profileContracts,
            subtitle: menuItems.contracts.subtitle.isNotEmpty
                ? menuItems.contracts.subtitle
                : LocaleKeys.profileContractCountLabel.replaceAll(
                    '{count}',
                    '${menuItems.contracts.count}',
                  ),
            iconColor: context.appColor(AppColors.blue),
            iconBackgroundColor: context.appColor(
              AppColors.bluePale,
              surface: true,
            ),
            onTap: () => Go.to(const ProfileContractsScreen()),
          ),
        ),
        ProfileSurfaceCard(
          padding: EdgeInsets.symmetric(horizontal: 16.w, vertical: 2.h),
          child: ProfileMenuTile(
            icon: Icons.star_outline_rounded,
            label: menuItems.reviews.title.isNotEmpty
                ? menuItems.reviews.title
                : LocaleKeys.profileMyReviews,
            subtitle: menuItems.reviews.subtitle.isNotEmpty
                ? menuItems.reviews.subtitle
                : LocaleKeys.profileReviewCountLabel.replaceAll(
                    '{count}',
                    '${menuItems.reviews.count}',
                  ),
            iconColor: context.appColor(AppColors.amber),
            iconBackgroundColor: context.appColor(
              AppColors.orangePale,
              surface: true,
            ),
            onTap: () => Go.to(const MyReviewsScreen()),
          ),
        ),
        ProfileSurfaceCard(
          child: ProfileMenuTile(
            icon: Icons.account_circle_outlined,
            label: LocaleKeys.profileSummaryTitle,
            iconColor: context.appColor(AppColors.sokoonTeal),
            iconBackgroundColor: context.appColor(
              AppColors.mintLight,
              surface: true,
            ),
            onTap: () => Go.to(const TenantAccountSummaryScreen()),
          ),
        ),
      ],
    );
  }
}
