part of '../../../imports.dart';

class VisitPrivacyBanner extends StatelessWidget {
  const VisitPrivacyBanner({super.key});

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: EdgeInsets.symmetric(horizontal: 13.w, vertical: 12.h),
      decoration: BoxDecoration(
        color: context.appColor(AppColors.bluePale, surface: true),
        borderRadius: BorderRadius.circular(14.r),
      ),
      child: Row(
        spacing: 8.w,
        children: [
          Icon(
            Icons.privacy_tip_outlined,
            color: context.appColor(AppColors.blue),
            size: 16.r,
          ),
          Expanded(
            child: AppText(
              LocaleKeys.tenantVisitPrivacyMessage,
              style: AppTextStyles.semiBold.copyWith(
                color: context.appColor(AppColors.blue),
                fontSize: 12.sp,
              ),
              maxLines: 2,
            ),
          ),
        ],
      ),
    );
  }
}
