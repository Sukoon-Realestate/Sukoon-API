part of '../../../imports.dart';

class ProfileContractsEmptyState extends StatelessWidget {
  const ProfileContractsEmptyState({super.key});
  @override
  Widget build(BuildContext context) => Center(
    child: SingleChildScrollView(
      child: Column(
        mainAxisSize: MainAxisSize.min,
        children: [
          ExcludeSemantics(
            child: Assets.lottie.emptyBox.lottie(
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
            LocaleKeys.profileContractsEmptyTitle,
            textAlign: TextAlign.center,
            style: AppTextStyles.bold16.copyWith(color: AppColors.sokoonNavy),
          ),
          8.szH,
          AppText(
            LocaleKeys.profileContractsEmptyDescription,
            textAlign: TextAlign.center,
            style: AppTextStyles.regular14.copyWith(
              color: AppColors.sokoonGray,
              height: 1.5,
            ),
          ),
        ],
      ).paddingAll(24),
    ),
  );
}
