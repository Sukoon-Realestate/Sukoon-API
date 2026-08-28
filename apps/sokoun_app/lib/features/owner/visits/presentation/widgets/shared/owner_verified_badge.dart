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
        color: AppColors.sokoonTeal,
        fontSize: 10.sp,
        fontWeight: FontWeight.w900,
      ),
    );
  }
}
