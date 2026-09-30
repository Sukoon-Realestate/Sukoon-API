part of '../../../imports.dart';

class OwnerAnalyticsBarChart extends StatelessWidget {
  const OwnerAnalyticsBarChart({super.key, required this.values});

  final List<int> values;

  @override
  Widget build(BuildContext context) {
    final int maximum = values.isEmpty
        ? 1
        : values.reduce((current, next) => current > next ? current : next);

    return Container(
      padding: EdgeInsets.all(16.w),
      decoration: BoxDecoration(
        color: AppColors.white,
        borderRadius: BorderRadius.circular(18.r),
        border: Border.all(color: AppColors.sokoonBorder),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          AppText(
            LocaleKeys.ownerAnalyticsViewsLastFourteenDays,
            style: AppTextStyles.bold15.copyWith(
              color: AppColors.sokoonNavy,
              fontSize: 15.sp,
              height: 1.45,
            ),
          ),
          18.szH,
          SizedBox(
            height: 128.h,
            child: Row(
              crossAxisAlignment: CrossAxisAlignment.end,
              spacing: 5.w,
              children: [
                for (int index = 0; index < values.length; index++)
                  Expanded(
                    child: AnimatedContainer(
                      duration: SokounMotion.duration(
                        context,
                        milliseconds: 250,
                      ),
                      height: (values[index] / maximum) * 112.h,
                      decoration: BoxDecoration(
                        color: index == values.length - 1
                            ? AppColors.sokoonTeal
                            : AppColors.tealAlpha19,
                        borderRadius: BorderRadius.vertical(
                          top: Radius.circular(5.r),
                        ),
                      ),
                    ),
                  ),
              ],
            ),
          ),
          8.szH,
          Row(
            children: [
              AppText(
                LocaleKeys.ownerAnalyticsFourteenDaysAgo,
                style: AppTextStyles.regular10.copyWith(
                  color: AppColors.sokoonMuted,
                  fontSize: 10.sp,
                  height: 1.45,
                ),
              ),
              const Spacer(),
              AppText(
                LocaleKeys.ownerAnalyticsToday,
                style: AppTextStyles.regular10.copyWith(
                  color: AppColors.sokoonMuted,
                  fontSize: 10.sp,
                  height: 1.45,
                ),
              ),
            ],
          ),
        ],
      ),
    );
  }
}
