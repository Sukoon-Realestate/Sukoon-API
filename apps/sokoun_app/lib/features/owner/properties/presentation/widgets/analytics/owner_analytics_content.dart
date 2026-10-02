part of '../../../imports.dart';

class OwnerAnalyticsContent extends StatelessWidget {
  const OwnerAnalyticsContent({
    super.key,
    required this.propertyTitle,
    required this.analytics,
  });
  final String propertyTitle;
  final OwnerPropertyAnalyticsContent analytics;

  @override
  Widget build(BuildContext context) {
    final content = analytics;
    if (!content.hasDetails) {
      return OwnerAnalyticsUnavailableDetails(
        propertyTitle: propertyTitle,
        views: content.views,
      );
    }
    return ListView(
      padding: EdgeInsets.fromLTRB(20.w, 16.h, 20.w, 24.h),
      children: [
        AppText(
          propertyTitle,
          style: AppTextStyles.semiBold.copyWith(
            color: AppColors.sokoonNavy,
            fontSize: 16.sp,
          ),
        ),
        if (content.periodLabel.isNotEmpty)
          AppText(content.periodLabel, style: AppTextStyles.regular13),
        14.szH,
        SokounAdaptiveGrid(
          minimumWidth: 150,
          maximumColumns: 4,
          children: [
            OwnerAnalyticsMetricCard(
              label: LocaleKeys.ownerAnalyticsViews,
              value: content.views.toString(),
              icon: Icons.visibility_outlined,
              color: AppColors.blue,
              backgroundColor: AppColors.bluePale,
            ),
            OwnerAnalyticsMetricCard(
              label: LocaleKeys.ownerAnalyticsVisitRequests,
              value: content.visitRequests.toString(),
              icon: Icons.event_available_outlined,
              color: AppColors.sokoonTeal,
              backgroundColor: AppColors.mintLight,
            ),
            OwnerAnalyticsMetricCard(
              label: LocaleKeys.ownerAnalyticsSaved,
              value: content.saves.toString(),
              icon: Icons.favorite_border_rounded,
              color: AppColors.red,
              backgroundColor: AppColors.redPale,
            ),
            OwnerAnalyticsMetricCard(
              label: LocaleKeys.ownerAnalyticsAcceptanceRate,
              value: '${_ownerFormattedNumber(content.acceptanceRate)}%',
              icon: Icons.trending_up_rounded,
              color: AppColors.green,
              backgroundColor: AppColors.greenPale,
            ),
          ],
        ),
        14.szH,
        if (content.history.isNotEmpty)
          OwnerAnalyticsBarChart(
            values: content.viewHistory,
            dates: content.history.map((day) => day.date).toList(),
          ),
        if (content.history.isEmpty && content.criteria.isEmpty)
          const OwnerAnalyticsEmptyState(),
        if (content.criteria.isNotEmpty) ...[
          14.szH,
          OwnerPropertyInterestCard(
            items: content.criteria
                .map(
                  (item) => OwnerPropertyInterestItem(
                    label: item.label,
                    value: item.percentage,
                  ),
                )
                .toList(growable: false),
          ),
        ],
      ],
    );
  }
}
