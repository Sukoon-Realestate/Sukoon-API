part of '../../../imports.dart';

class ProfileLogoutSheet extends StatelessWidget {
  const ProfileLogoutSheet({super.key});
  @override
  Widget build(BuildContext context) => SafeArea(
    child: SokounContent(
      width: SokounContentWidth.form,
      child: SingleChildScrollView(
        child: Column(
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment: CrossAxisAlignment.stretch,
          spacing: 18.h,
          children: [
            Icon(Icons.logout_rounded, size: 36.r, color: AppColors.sokoonRose),
            AppText(
              LocaleKeys.settingsLogoutTitle,
              textAlign: TextAlign.center,
              style: AppTextStyles.bold16.copyWith(color: AppColors.sokoonNavy),
            ),
            AppText(
              LocaleKeys.settingsLogoutDescription,
              textAlign: TextAlign.center,
              style: AppTextStyles.regular14.copyWith(
                color: AppColors.sokoonGray,
                height: 1.5,
              ),
            ),
            DefaultButton(
              title: LocaleKeys.profileLogout,
              color: AppColors.sokoonRose,
              onTap: () => Go.back(true),
            ),
            DefaultButton(
              title: LocaleKeys.cancel,
              color: AppColors.white,
              textColor: AppColors.sokoonNavy,
              onTap: () => Go.back(false),
            ),
          ],
        ).paddingAll(24),
      ),
    ),
  );
}
