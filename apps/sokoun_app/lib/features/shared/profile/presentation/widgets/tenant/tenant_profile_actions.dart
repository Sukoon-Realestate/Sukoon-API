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
            icon: Icons.calendar_month_outlined,
            label: menuItems.visitRequests.title.isNotEmpty
                ? menuItems.visitRequests.title
                : LocaleKeys.tenantVisitsTitle,
            subtitle: menuItems.visitRequests.subtitle.isNotEmpty
                ? menuItems.visitRequests.subtitle
                : '${menuItems.visitRequests.count}',
            iconColor: AppColors.sokoonTeal,
            iconBackgroundColor: AppColors.mintLight,
            onTap: () => Go.to(const TenantVisitsScreen()),
          ),
        ),
        ProfileSurfaceCard(
          padding: EdgeInsets.symmetric(horizontal: 16.w, vertical: 2.h),
          child: ProfileMenuTile(
            icon: Icons.shield_outlined,
            label: menuItems.verification.title.isNotEmpty
                ? menuItems.verification.title
                : LocaleKeys.profileVerificationDocuments,
            subtitle: menuItems.verification.subtitle.isNotEmpty
                ? menuItems.verification.subtitle
                : menuItems.verification.isVerified
                ? LocaleKeys.verified
                : LocaleKeys.ownerHomeUnverified,
            iconColor: AppColors.sokoonTeal,
            iconBackgroundColor: AppColors.mintLight,
            onTap: () => Go.to(const KycIntroScreen()),
          ),
        ),
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
            iconColor: AppColors.blue,
            iconBackgroundColor: AppColors.bluePale,
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
            iconColor: AppColors.amber,
            iconBackgroundColor: AppColors.orangePale,
            onTap: () => Go.to(const MyReviewsScreen()),
          ),
        ),
        ProfileSurfaceCard(
          child: ProfileMenuTile(
            icon: Icons.settings_outlined,
            label: LocaleKeys.profileSettingsTitle,
            iconColor: AppColors.sokoonTeal,
            iconBackgroundColor: AppColors.mintLight,
            onTap: () => Go.to(const ProfileSettingsScreen()),
          ),
        ),
        ProfileSurfaceCard(
          padding: EdgeInsets.symmetric(vertical: 2.h),
          child: const PublicPageMenu(),
        ),
      ],
    );
  }
}
