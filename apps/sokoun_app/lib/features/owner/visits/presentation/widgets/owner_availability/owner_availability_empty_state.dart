part of '../../../imports.dart';

class OwnerAvailabilityEmptyState extends StatelessWidget {
  const OwnerAvailabilityEmptyState({super.key});

  @override
  Widget build(BuildContext context) => SingleChildScrollView(
    padding: EdgeInsets.symmetric(horizontal: 32.w, vertical: 24.h),
    child: Column(
      mainAxisSize: MainAxisSize.min,
      children: [
        ExcludeSemantics(
          child: Assets.lottie.noData.lottie(
            width: 140.r,
            height: 116.r,
            animate: !MediaQuery.of(context).disableAnimations,
            repeat: false,
            package: 'melos_core',
          ),
        ),
        10.szH,
        AppText(
          LocaleKeys.ownerAvailabilityEmptyTitle,
          style: AppTextStyles.bold.copyWith(
            color: context.appColor(AppColors.sokoonNavy),
            fontSize: 17.sp,
          ),
          textAlign: TextAlign.center,
        ),
        7.szH,
        AppText(
          LocaleKeys.ownerAvailabilityEmptyDescription,
          style: AppTextStyles.medium13.copyWith(
            color: context.appColor(AppColors.sokoonGray),
            fontSize: 13.sp,
            height: 1.45,
          ),
          textAlign: TextAlign.center,
        ),
      ],
    ),
  ).centerWidget;
}
