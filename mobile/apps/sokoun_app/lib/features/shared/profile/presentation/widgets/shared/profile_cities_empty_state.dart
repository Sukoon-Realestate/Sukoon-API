part of '../../../imports.dart';

class ProfileCitiesEmptyState extends StatelessWidget {
  const ProfileCitiesEmptyState({super.key});
  @override
  Widget build(BuildContext context) => SingleChildScrollView(
    padding: EdgeInsets.all(24.w),
    child: Column(
      children: [
        ExcludeSemantics(
          child: Assets.lottie.noData.lottie(
            width: 140.r,
            height: 116.r,
            animate: !MediaQuery.disableAnimationsOf(context),
            repeat: false,
            package: 'melos_core',
          ),
        ),
        AppText(
          LocaleKeys.profileCitiesEmptyTitle,
          style: AppTextStyles.bold16,
          textAlign: TextAlign.center,
        ),
      ],
    ),
  );
}
