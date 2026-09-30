part of '../../../imports.dart';

class OwnerReviewsEmptyState extends StatelessWidget {
  const OwnerReviewsEmptyState({super.key});

  @override
  Widget build(BuildContext context) {
    final bool reduceMotion = MediaQuery.of(context).disableAnimations;
    return Semantics(
      label: LocaleKeys.profileNoReviewsTitle,
      child: Padding(
        padding: EdgeInsets.symmetric(vertical: 8.h),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          spacing: 4.h,
          children: [
            ExcludeSemantics(
              child: Assets.lottie.noData.lottie(
                width: 104.r,
                height: 82.r,
                animate: !reduceMotion,
                repeat: false,
                fit: BoxFit.contain,
                package: 'melos_core',
              ),
            ),
            AppText(
              LocaleKeys.profileNoReviewsTitle,
              style: AppTextStyles.extraBold.copyWith(
                color: AppColors.sokoonNavy,
                fontSize: 14.sp,
              ),
              textAlign: TextAlign.center,
            ),
            AppText(
              LocaleKeys.profileNoReviewsDescription,
              style: AppTextStyles.regular11.copyWith(
                color: AppColors.sokoonGray,
                fontSize: 11.sp,
                height: 1.45,
              ),
              textAlign: TextAlign.center,
              maxLines: 2,
            ),
          ],
        ),
      ),
    );
  }
}
