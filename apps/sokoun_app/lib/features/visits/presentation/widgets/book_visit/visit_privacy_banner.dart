part of '../../../imports.dart';

class VisitPrivacyBanner extends StatelessWidget {
  const VisitPrivacyBanner({super.key});

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: EdgeInsets.symmetric(horizontal: 13.w, vertical: 12.h),
      decoration: BoxDecoration(
        color: AppColors.bluePale,
        borderRadius: BorderRadius.circular(14.r),
      ),
      child: Row(
        children: [
          Icon(Icons.privacy_tip_outlined, color: AppColors.blue, size: 16.r),
          8.szW,
          Expanded(
            child: AppText(
              LocaleKeys.tenantVisitPrivacyMessage,
              color: AppColors.blue,
              fontSize: 12.sp,
              fontWeight: FontWeight.w600,
              maxLines: 2,
            ),
          ),
        ],
      ),
    );
  }
}
