part of '../../../imports.dart';

class TenantAccountSummaryContentView extends StatelessWidget {
  const TenantAccountSummaryContentView({super.key, required this.summary});

  final TenantAccountSummaryContent summary;

  String _shortcutLabel(TenantAccountSummaryShortcutContent shortcut) {
    return shortcut.label.isNotEmpty
        ? shortcut.label
        : shortcut.count.toString();
  }

  @override
  Widget build(BuildContext context) {
    final TenantAccountSummaryShortcutsContent shortcuts = summary.shortcuts;

    return ListView(
      padding: EdgeInsets.all(20.r),
      children: [
        TenantSummaryHeaderCard(user: summary.user),
        18.szH,
        TenantIdentityVerificationCard(
          verification: summary.identityVerification,
        ),
        18.szH,
        ProfileStatGrid(
          withCards: true,
          valueColor: AppColors.sokoonTeal,
          stats: [
            ProfileStat(
              value: summary.stats.savedPropertiesCount.toString(),
              label: LocaleKeys.profileSavedProperties,
            ),
            ProfileStat(
              value: summary.stats.completedVisitsCount.toString(),
              label: LocaleKeys.profileCompletedVisits,
            ),
            ProfileStat(
              value: summary.stats.activeChatsCount.toString(),
              label: LocaleKeys.profileActiveChats,
            ),
          ],
        ),
        18.szH,
        ProfileSurfaceCard(
          padding: EdgeInsets.symmetric(horizontal: 16.w, vertical: 2.h),
          child: Column(
            children: [
              ProfileMenuTile(
                icon: Icons.favorite_border_rounded,
                label: shortcuts.savedProperties.title.isNotEmpty
                    ? shortcuts.savedProperties.title
                    : LocaleKeys.profileSavedProperties,
                value: _shortcutLabel(shortcuts.savedProperties),
                iconColor: AppColors.sokoonTeal,
                iconBackgroundColor: AppColors.mintLight,
                onTap: () => Go.to(const FavoritesScreen()),
                showDivider: true,
              ),
              ProfileMenuTile(
                icon: Icons.calendar_month_outlined,
                label: shortcuts.visitsHistory.title.isNotEmpty
                    ? shortcuts.visitsHistory.title
                    : LocaleKeys.profileVisitHistory,
                value: _shortcutLabel(shortcuts.visitsHistory),
                iconColor: AppColors.sokoonTeal,
                iconBackgroundColor: AppColors.mintLight,
                onTap: () => Go.to(const TenantVisitsScreen()),
                showDivider: true,
              ),
              ProfileMenuTile(
                icon: Icons.shield_outlined,
                label: shortcuts.identityVerification.title.isNotEmpty
                    ? shortcuts.identityVerification.title
                    : LocaleKeys.profileIdentityVerification,
                value: shortcuts.identityVerification.label.isNotEmpty
                    ? shortcuts.identityVerification.label
                    : summary.identityVerification.statusLabel,
                iconColor: summary.identityVerification.isVerified
                    ? AppColors.green
                    : AppColors.sokoonGray,
                iconBackgroundColor: summary.identityVerification.isVerified
                    ? AppColors.greenPale
                    : AppColors.grayBackground,
                onTap: () => Go.to(
                  summary.identityVerification.isVerified
                      ? const KycApprovedScreen()
                      : const KycIntroScreen(),
                ),
              ),
            ],
          ),
        ),
      ],
    );
  }
}
