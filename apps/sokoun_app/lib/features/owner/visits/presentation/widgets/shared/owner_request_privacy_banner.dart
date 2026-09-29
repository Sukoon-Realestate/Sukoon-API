part of '../../../imports.dart';

class OwnerRequestPrivacyBanner extends StatelessWidget {
  const OwnerRequestPrivacyBanner({
    super.key,
    required this.message,
    this.icon = Icons.lock_outline_rounded,
  });

  final String message;
  final IconData icon;

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
          Icon(icon, color: AppColors.blue, size: 17.r),
          9.szW,
          Expanded(
            child: AppText(
              message,
              style: AppTextStyles.semiBold.copyWith(
                color: AppColors.blue,
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
