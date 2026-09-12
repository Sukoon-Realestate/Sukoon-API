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
            4.szH,
            AppText(
              LocaleKeys.profileNoReviewsTitle,
              color: AppColors.sokoonNavy,
              fontSize: 14.sp,
              fontWeight: FontWeight.w800,
              textAlign: TextAlign.center,
            ),
            4.szH,
            AppText(
              LocaleKeys.profileNoReviewsDescription,
              color: AppColors.sokoonGray,
              fontSize: 11.sp,
              textAlign: TextAlign.center,
              maxLines: 2,
            ),
          ],
        ),
      ),
    );
  }
}
