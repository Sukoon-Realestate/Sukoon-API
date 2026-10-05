part of '../../../imports.dart';

class OwnerAnalyticsBarChart extends StatelessWidget {
  const OwnerAnalyticsBarChart({
    super.key,
    required this.values,
    this.dates = const [],
  });

  final List<int> values;
  final List<String> dates;

  @override
  Widget build(BuildContext context) {
    final int maximum = values.isEmpty
        ? 1
        : values.fold<int>(
            1,
            (current, next) => current > next ? current : next,
          );

    return Container(
      padding: EdgeInsets.all(16.w),
      decoration: BoxDecoration(
        color: context.appColor(AppColors.white, surface: true),
        borderRadius: BorderRadius.circular(18.r),
        border: Border.all(color: context.appColor(AppColors.sokoonBorder)),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          AppText(
            LocaleKeys.ownerAnalyticsViews,
            style: AppTextStyles.bold15.copyWith(
              color: context.appColor(AppColors.sokoonNavy),
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
                            ? context.appColor(
                                AppColors.sokoonTeal,
                                surface: true,
                              )
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
          if (dates.isNotEmpty) ...[
            8.szH,
            Row(
              children: [
                Expanded(
                  child: AppText(dates.first, style: AppTextStyles.regular11),
                ),
                Expanded(
                  child: AppText(
                    dates.last,
                    style: AppTextStyles.regular11,
                    textAlign: TextAlign.end,
                  ),
                ),
              ],
            ),
          ],
        ],
      ),
    );
  }
}
