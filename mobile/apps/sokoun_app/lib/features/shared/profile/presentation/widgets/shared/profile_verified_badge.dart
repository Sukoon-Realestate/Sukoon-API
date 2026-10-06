part of '../../../imports.dart';

class ProfileVerifiedBadge extends StatelessWidget {
  const ProfileVerifiedBadge({super.key, this.text, required this.isVerified});

  final String? text;
  final bool isVerified;

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: EdgeInsets.symmetric(horizontal: 8.w, vertical: 3.h),
      decoration: BoxDecoration(
        color: isVerified
            ? context.appColor(AppColors.goldPale, surface: true)
            : context.appColor(AppColors.grayBackground, surface: true),
        borderRadius: BorderRadius.circular(999.r),
      ),
      child: Row(
        mainAxisSize: MainAxisSize.min,
        spacing: 4.w,
        children: [
          Icon(
            isVerified
                ? Icons.check_circle_outline_rounded
                : Icons.shield_outlined,
            color: isVerified
                ? AppColors.sokoonGold
                : context.appColor(AppColors.sokoonGray),
            size: 11.r,
          ),
          Flexible(
            child: AppText(
              text ?? LocaleKeys.verified,
              style: AppTextStyles.bold10.copyWith(
                color: isVerified
                    ? context.appColor(AppColors.sokoonNavy)
                    : context.appColor(AppColors.sokoonGray),
                fontSize: 10.sp,
                height: 1.45,
              ),
              maxLines: 1,
              overflow: TextOverflow.ellipsis,
            ),
          ),
        ],
      ),
    );
  }
}
