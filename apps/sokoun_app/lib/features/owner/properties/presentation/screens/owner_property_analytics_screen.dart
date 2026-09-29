part of '../../imports.dart';

class OwnerPropertyAnalyticsScreen extends StatelessWidget {
  const OwnerPropertyAnalyticsScreen({
    super.key,
    required this.property,
    required this.analytics,
  });

  final OwnerPropertyContent property;
  final OwnerPropertyAnalyticsContent analytics;

  @override
  Widget build(BuildContext context) {
    final OwnerPropertyAnalyticsContent content = analytics;

    return AppScaffold(
      showBackButton: false,
      contentWidth: SokounContentWidth.wide,
      backgroundColor: AppColors.scaffoldBackground,
      body: SafeArea(
        child: Column(
          children: [
            OwnerPropertyTopBar(
              title: LocaleKeys.ownerAnalyticsTitle,
              trailing: Container(
                alignment: Alignment.center,
                padding: EdgeInsets.symmetric(horizontal: 8.w, vertical: 5.h),
                decoration: BoxDecoration(
                  color: AppColors.grayBackground,
                  borderRadius: BorderRadius.circular(99.r),
                ),
                child: AppText(
                  LocaleKeys.ownerAnalyticsThirtyDays,
                  style: AppTextStyles.bold11.copyWith(
                    color: AppColors.sokoonGray,
                    fontSize: 11.sp,
                    height: 1.45,
                  ),
                ),
              ),
            ),
            Expanded(
              child: ListView(
                padding: EdgeInsets.fromLTRB(20.w, 4.h, 20.w, 24.h),
                children: [
                  AppText(
                    property.title,
                    style: AppTextStyles.semiBold.copyWith(
                      color: AppColors.sokoonGray,
                      fontSize: 13.sp,
                    ),
                    textAlign: TextAlign.center,
                  ),
                  14.szH,
                  GridView.count(
                    crossAxisCount: 2,
                    shrinkWrap: true,
                    physics: const NeverScrollableScrollPhysics(),
                    crossAxisSpacing: 10.w,
                    mainAxisSpacing: 10.h,
                    childAspectRatio: 1.02,
                    children: [
                      OwnerAnalyticsMetricCard(
                        label: LocaleKeys.ownerAnalyticsViews,
                        value: _formatNumber(content.views),
                        icon: Icons.visibility_outlined,
                        color: AppColors.blue,
                        backgroundColor: AppColors.bluePale,
                      ),
                      OwnerAnalyticsMetricCard(
                        label: LocaleKeys.ownerAnalyticsVisitRequests,
                        value: '${content.visitRequests}',
                        icon: Icons.event_available_outlined,
                        color: AppColors.sokoonTeal,
                        backgroundColor: AppColors.mintLight,
                      ),
                      OwnerAnalyticsMetricCard(
                        label: LocaleKeys.ownerAnalyticsSaved,
                        value: '${content.saves}',
                        icon: Icons.favorite_border_rounded,
                        color: AppColors.red,
                        backgroundColor: AppColors.redPale,
                      ),
                      OwnerAnalyticsMetricCard(
                        label: LocaleKeys.ownerAnalyticsAcceptanceRate,
                        value: '${content.acceptanceRate}%',
                        icon: Icons.trending_up_rounded,
                        color: AppColors.green,
                        backgroundColor: AppColors.greenPale,
                      ),
                    ],
                  ),
                  14.szH,
                  OwnerAnalyticsBarChart(values: content.viewHistory),
                  14.szH,
                  OwnerPropertyInterestCard(
                    items: [
                      OwnerPropertyInterestItem(
                        label: LocaleKeys.ownerAnalyticsInterestArea,
                        value: content.spaceInterest,
                      ),
                      OwnerPropertyInterestItem(
                        label: LocaleKeys.ownerAnalyticsInterestPrice,
                        value: content.priceInterest,
                      ),
                      OwnerPropertyInterestItem(
                        label: LocaleKeys.ownerAnalyticsInterestLocation,
                        value: content.locationInterest,
                      ),
                      OwnerPropertyInterestItem(
                        label: LocaleKeys.ownerAnalyticsInterestAmenities,
                        value: content.amenitiesInterest,
                      ),
                    ],
                  ),
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }

  String _formatNumber(int value) {
    return value.toString().replaceAllMapped(
      RegExp(r'(\d)(?=(\d{3})+(?!\d))'),
      (match) => '${match[1]},',
    );
  }
}
