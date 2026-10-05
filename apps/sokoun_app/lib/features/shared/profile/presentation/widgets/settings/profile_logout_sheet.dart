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
            Icon(
              Icons.logout_rounded,
              size: 36.r,
              color: context.appColor(AppColors.sokoonRose),
            ),
            AppText(
              LocaleKeys.settingsLogoutTitle,
              textAlign: TextAlign.center,
              style: AppTextStyles.bold16.copyWith(
                color: context.appColor(AppColors.sokoonNavy),
              ),
            ),
            AppText(
              LocaleKeys.settingsLogoutDescription,
              textAlign: TextAlign.center,
              style: AppTextStyles.regular14.copyWith(
                color: context.appColor(AppColors.sokoonGray),
                height: 1.5,
              ),
            ),
            DefaultButton(
              title: LocaleKeys.profileLogout,
              color: context.appColor(AppColors.sokoonRose, surface: true),
              onTap: () => Go.back(true),
            ),
            DefaultButton(
              title: LocaleKeys.cancel,
              color: context.appColor(AppColors.white, surface: true),
              textColor: context.appColor(AppColors.sokoonNavy),
              onTap: () => Go.back(false),
            ),
          ],
        ).paddingAll(24),
      ),
    ),
  );
}
