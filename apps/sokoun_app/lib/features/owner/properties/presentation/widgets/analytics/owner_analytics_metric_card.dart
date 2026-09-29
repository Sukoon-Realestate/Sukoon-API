part of '../../../imports.dart';

class OwnerAnalyticsMetricCard extends StatelessWidget {
  const OwnerAnalyticsMetricCard({
    super.key,
    required this.label,
    required this.value,
    required this.icon,
    required this.color,
    required this.backgroundColor,
  });

  final String label;
  final String value;
  final IconData icon;
  final Color color;
  final Color backgroundColor;

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: EdgeInsets.all(14.w),
      decoration: BoxDecoration(
        color: AppColors.white,
        borderRadius: BorderRadius.circular(18.r),
        border: Border.all(color: AppColors.sokoonBorder),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Container(
            width: 36.r,
            height: 36.r,
            decoration: BoxDecoration(
              color: backgroundColor,
              borderRadius: BorderRadius.circular(11.r),
            ),
            child: Icon(icon, color: color, size: 20.r),
          ),
          10.szH,
          AppText(
            value,
            style: AppTextStyles.extraBold.copyWith(
              color: AppColors.sokoonNavy,
              fontSize: 21.sp,
            ),
          ),
          2.szH,
          AppText(
            label,
            style: AppTextStyles.semiBold.copyWith(
              color: AppColors.sokoonGray,
              fontSize: 12.sp,
            ),
          ),
        ],
      ),
    );
  }
}
