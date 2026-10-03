part of '../../../imports.dart';

class OwnerVerifiedBadge extends StatelessWidget {
  const OwnerVerifiedBadge({super.key});

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: EdgeInsets.symmetric(horizontal: 8.w, vertical: 3.h),
      decoration: BoxDecoration(
        color: AppColors.tealAlpha07,
        borderRadius: BorderRadius.circular(8.r),
      ),
      child: AppText(
        LocaleKeys.ownerVisitVerified,
        style: AppTextStyles.bold10.copyWith(
          color: AppColors.sokoonTeal,
          fontSize: 12.sp,
          height: 1.45,
        ),
      ),
    );
  }
}
