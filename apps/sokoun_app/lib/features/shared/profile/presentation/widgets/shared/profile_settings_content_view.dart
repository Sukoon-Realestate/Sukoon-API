part of '../../../imports.dart';

class ProfileSettingsContentView extends StatelessWidget {
  const ProfileSettingsContentView({super.key, required this.workspace});
  final AppWorkspace workspace;
  @override
  Widget build(BuildContext context) => ListView(
    padding: EdgeInsets.all(20.r),
    children: [
      AppText(
        workspace.isOwner
            ? LocaleKeys.settingsOwnerIntro
            : LocaleKeys.settingsTenantIntro,
        style: AppTextStyles.regular14.copyWith(
          color: AppColors.sokoonGray,
          height: 1.5,
        ),
      ),
      20.szH,
      ProfileMenuSection(
        title: LocaleKeys.settingsPreferences,
        items: [
          ProfileMenuItem(
            icon: Icons.language_rounded,
            label: LocaleKeys.changeLanguage,
            color: AppColors.sokoonTeal,
            backgroundColor: AppColors.mintLight,
            onTap: () => Go.to(const LanguageSelectionScreen()),
          ),
          ProfileMenuItem(
            icon: Icons.notifications_outlined,
            label: LocaleKeys.notificationSettingsTitle,
            color: AppColors.sokoonTeal,
            backgroundColor: AppColors.mintLight,
            onTap: () => Go.to(
              NotificationSettingsScreen(
                role: workspace.isOwner
                    ? NotificationRole.owner
                    : NotificationRole.tenant,
              ),
            ),
          ),
        ],
      ),
      18.szH,
      ProfileMenuSection(
        title: LocaleKeys.settingsSecurity,
        items: [
          ProfileMenuItem(
            icon: Icons.privacy_tip_outlined,
            label: LocaleKeys.settingsPrivacyOptions,
            color: AppColors.sokoonTeal,
            backgroundColor: AppColors.mintLight,
            onTap: () => Go.to(ProfilePrivacyScreen(workspace: workspace)),
          ),
          ProfileMenuItem(
            icon: Icons.lock_outline_rounded,
            label: LocaleKeys.settingsChangePassword,
            color: AppColors.sokoonTeal,
            backgroundColor: AppColors.mintLight,
            onTap: () => Go.to(const ChangePasswordScreen()),
          ),
        ],
      ),
      18.szH,
      AppText(
        LocaleKeys.settingsLegal,
        style: AppTextStyles.bold12.copyWith(color: AppColors.sokoonGray),
      ),
      8.szH,
      const ProfileSurfaceCard(child: PublicPageMenu()),
      24.szH,
      const ProfileLogoutButton(),
      12.szH,
      const ProfileDeleteAccountButton(),
    ],
  );
}
