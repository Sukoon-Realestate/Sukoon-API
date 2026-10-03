part of '../../../imports.dart';

class ProfileDeletionContent extends StatelessWidget {
  const ProfileDeletionContent({super.key});
  @override
  Widget build(BuildContext context) => Column(
    crossAxisAlignment: CrossAxisAlignment.stretch,
    spacing: 18.h,
    children: [
      Container(
        padding: EdgeInsets.all(20.r),
        decoration: BoxDecoration(
          color: AppColors.redPale,
          borderRadius: BorderRadius.circular(16.r),
        ),
        child: Column(
          spacing: 12.h,
          children: [
            Icon(
              Icons.warning_amber_rounded,
              color: AppColors.sokoonRose,
              size: 36.r,
            ),
            AppText(
              LocaleKeys.settingsDeleteWarning,
              textAlign: TextAlign.center,
              style: AppTextStyles.bold16.copyWith(color: AppColors.sokoonRose),
            ),
            AppText(
              LocaleKeys.deletingWillRemoveAllYourData,
              textAlign: TextAlign.center,
              style: AppTextStyles.regular14.copyWith(
                color: AppColors.sokoonNavy,
                height: 1.6,
              ),
            ),
          ],
        ),
      ),
      AppText(
        LocaleKeys.settingsDeleteConsequences,
        style: AppTextStyles.bold16,
      ),
      for (final label in [
        LocaleKeys.settingsDeleteIdentity,
        LocaleKeys.settingsDeleteActivity,
        LocaleKeys.settingsDeleteListings,
      ])
        Row(
          crossAxisAlignment: CrossAxisAlignment.start,
          spacing: 10.w,
          children: [
            Icon(
              Icons.remove_circle_outline_rounded,
              color: AppColors.sokoonRose,
              size: 20.r,
            ),
            Expanded(
              child: AppText(
                label,
                style: AppTextStyles.regular14.copyWith(
                  color: AppColors.sokoonGray,
                  height: 1.5,
                ),
              ),
            ),
          ],
        ),
    ],
  );
}
