part of '../../../imports.dart';

class ProfileVerificationBanner extends StatelessWidget {
  const ProfileVerificationBanner({
    super.key,
    required this.title,
    required this.description,
    this.isPrivacy = false,
  });

  final String title;
  final String description;
  final bool isPrivacy;

  @override
  Widget build(BuildContext context) {
    final Color color = isPrivacy ? AppColors.blue : AppColors.green;
    final Color backgroundColor = isPrivacy
        ? AppColors.bluePale
        : AppColors.greenPale;

    return Container(
      width: double.infinity,
      padding: EdgeInsets.symmetric(horizontal: 16.w, vertical: 13.h),
      decoration: BoxDecoration(
        color: backgroundColor,
        borderRadius: BorderRadius.circular(14.r),
      ),
      child: Row(
        spacing: 10.w,
        children: [
          Icon(
            isPrivacy
                ? Icons.lock_outline_rounded
                : Icons.check_circle_outline_rounded,
            color: color,
            size: isPrivacy ? 17.r : 22.r,
          ),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              spacing: 2.h,
              children: [
                if (title.isNotEmpty)
                  AppText(
                    title,
                    style: AppTextStyles.extraBold13.copyWith(
                      color: color,
                      fontSize: 13.sp,
                      height: 1.45,
                    ),
                  ),
                AppText(
                  description,
                  style: AppTextStyles.regular11.copyWith(
                    color: isPrivacy ? color : AppColors.sokoonGray,
                    fontSize: 11.sp,
                    height: 1.35,
                    fontWeight: isPrivacy ? FontWeight.w600 : FontWeight.w400,
                  ),
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }
}
