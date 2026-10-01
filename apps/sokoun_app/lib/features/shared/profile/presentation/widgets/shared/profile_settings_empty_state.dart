part of '../../../imports.dart';

class ProfileSettingsEmptyState extends StatelessWidget {
  const ProfileSettingsEmptyState({super.key});
  @override
  Widget build(BuildContext context) => Center(
    child: SingleChildScrollView(
      padding: EdgeInsets.all(24.r),
      child: Column(
        mainAxisSize: MainAxisSize.min,
        children: [
          ExcludeSemantics(
            child: Assets.lottie.noData.lottie(
              width: 144.r,
              height: 120.r,
              package: 'melos_core',
              repeat: false,
              animate:
                  !MediaQuery.disableAnimationsOf(context) &&
                  !MediaQuery.accessibleNavigationOf(context),
            ),
          ),
          12.szH,
          AppText(
            LocaleKeys.profileSettingsEmptyTitle,
            textAlign: TextAlign.center,
            style: AppTextStyles.bold16.copyWith(color: AppColors.sokoonNavy),
          ),
          8.szH,
          AppText(
            LocaleKeys.profileSettingsEmptyDescription,
            textAlign: TextAlign.center,
            style: AppTextStyles.regular14.copyWith(
              color: AppColors.sokoonGray,
            ),
          ),
        ],
      ),
    ),
  );
}
