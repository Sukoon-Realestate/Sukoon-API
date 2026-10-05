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
    final Color color = isPrivacy
        ? context.appColor(AppColors.blue)
        : context.appColor(AppColors.green);
    final Color backgroundColor = isPrivacy
        ? context.appColor(AppColors.bluePale, surface: true)
        : context.appColor(AppColors.greenPale, surface: true);

    return Container(
      width: double.infinity,
      padding: EdgeInsets.symmetric(horizontal: 16.w, vertical: 13.h),
      decoration: BoxDecoration(
        color: context.appColor(backgroundColor, surface: true),
        borderRadius: BorderRadius.circular(14.r),
      ),
      child: Row(
        spacing: 10.w,
        children: [
          Icon(
            isPrivacy
                ? Icons.lock_outline_rounded
                : Icons.check_circle_outline_rounded,
            color: context.appColor(color),
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
                      color: context.appColor(color),
                      fontSize: 13.sp,
                      height: 1.45,
                    ),
                  ),
                AppText(
                  description,
                  style: AppTextStyles.regular11.copyWith(
                    color: isPrivacy
                        ? color
                        : context.appColor(AppColors.sokoonGray),
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
