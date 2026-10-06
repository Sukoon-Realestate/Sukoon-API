part of '../../../imports.dart';

class OwnerAnalyticsUnavailableDetails extends StatelessWidget {
  const OwnerAnalyticsUnavailableDetails({
    super.key,
    required this.propertyTitle,
    required this.views,
  });

  final String propertyTitle;
  final int views;

  @override
  Widget build(BuildContext context) => ListView(
    padding: EdgeInsets.symmetric(horizontal: 20.w, vertical: 16.h),
    children: [
      AppText(
        propertyTitle,
        style: AppTextStyles.semiBold.copyWith(
          color: context.appColor(AppColors.sokoonNavy),
          fontSize: 16.sp,
        ),
      ),
      14.szH,
      OwnerAnalyticsMetricCard(
        label: LocaleKeys.ownerAnalyticsViews,
        value: '$views',
        icon: Icons.visibility_outlined,
        color: context.appColor(AppColors.blue),
        backgroundColor: context.appColor(AppColors.bluePale, surface: true),
      ),
      14.szH,
      AppText(
        LocaleKeys.ownerAnalyticsUnavailableDescription,
        style: AppTextStyles.regular14.copyWith(
          color: context.appColor(AppColors.sokoonGray),
          fontSize: 14.sp,
          height: 1.45,
        ),
      ),
    ],
  );
}
