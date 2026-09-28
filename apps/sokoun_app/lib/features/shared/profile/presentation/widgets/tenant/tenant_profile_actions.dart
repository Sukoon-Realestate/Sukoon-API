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
            icon: Icons.language_rounded,
            label: LocaleKeys.changeLanguage,
            subtitle: context.locale == Languages.arabic.locale
                ? LocaleKeys.languageArabicName
                : LocaleKeys.languageEnglishNativeName,
            iconColor: AppColors.sokoonTeal,
            iconBackgroundColor: AppColors.mintLight,
            onTap: () => Go.to(const LanguageSelectionScreen()),
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
      ],
    );
  }
}
