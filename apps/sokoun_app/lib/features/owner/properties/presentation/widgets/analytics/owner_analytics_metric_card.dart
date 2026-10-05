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
        color: context.appColor(AppColors.white, surface: true),
        borderRadius: BorderRadius.circular(18.r),
        border: Border.all(color: context.appColor(AppColors.sokoonBorder)),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Container(
            width: 36.r,
            height: 36.r,
            decoration: BoxDecoration(
              color: context.appColor(backgroundColor, surface: true),
              borderRadius: BorderRadius.circular(11.r),
            ),
            child: Icon(icon, color: context.appColor(color), size: 20.r),
          ),
          10.szH,
          AppText(
            value,
            style: AppTextStyles.extraBold.copyWith(
              color: context.appColor(AppColors.sokoonNavy),
              fontSize: 21.sp,
            ),
          ),
          2.szH,
          AppText(
            label,
            style: AppTextStyles.semiBold.copyWith(
              color: context.appColor(AppColors.sokoonGray),
              fontSize: 12.sp,
            ),
          ),
        ],
      ),
    );
  }
}
