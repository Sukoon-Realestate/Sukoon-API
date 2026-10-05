part of '../../../imports.dart';

class OwnerRevenueContentView extends StatelessWidget {
  const OwnerRevenueContentView({super.key, required this.data});
  final OwnerRevenueContent data;
  @override
  Widget build(BuildContext context) => ListView(
    padding: EdgeInsets.fromLTRB(20.w, 16.h, 20.w, 24.h),
    children: [
      OwnerRevenueSummaryCard(data: data),
      22.szH,
      if (data.properties.isEmpty && data.transactions.isEmpty)
        const OwnerRevenueEmptyState(),
      if (data.properties.isNotEmpty) ...[
        AppText(LocaleKeys.ownerRevenueProperties, style: AppTextStyles.bold16),
        10.szH,
        for (final item in data.properties)
          OwnerRevenuePropertyCard(item: item).paddingBottom(10.h),
      ],
      if (data.transactions.isNotEmpty) ...[
        12.szH,
        AppText(
          LocaleKeys.ownerRevenueLatestTransactions,
          style: AppTextStyles.bold16,
        ),
        10.szH,
        Container(
          padding: EdgeInsets.all(16.w),
          decoration: BoxDecoration(
            color: context.appColor(AppColors.white, surface: true),
            borderRadius: BorderRadius.circular(18.r),
            border: Border.all(color: context.appColor(AppColors.sokoonBorder)),
          ),
          child: Column(
            children: [
              for (final item in data.transactions) ...[
                OwnerTransactionRow(transaction: item),
                if (item != data.transactions.last)
                  Divider(
                    height: 24,
                    color: context.appColor(AppColors.sokoonBorder),
                  ),
              ],
            ],
          ),
        ),
      ],
    ],
  );
}

class OwnerRevenueSummaryCard extends StatelessWidget {
  const OwnerRevenueSummaryCard({super.key, required this.data});
  final OwnerRevenueContent data;
  @override
  Widget build(BuildContext context) => Container(
    padding: EdgeInsets.all(20.w),
    decoration: BoxDecoration(
      color: context.appColor(AppColors.sokoonTeal, surface: true),
      borderRadius: BorderRadius.circular(20.r),
    ),
    child: Column(
      spacing: 8.h,
      children: [
        AppText(
          LocaleKeys.ownerRevenueThisMonth,
          style: AppTextStyles.bold13.copyWith(color: AppColors.white),
        ),
        AppText(
          EgyptianPoundText.format(data.totalThisMonth),
          style: AppTextStyles.extraBold.copyWith(
            color: AppColors.white,
            fontSize: 30.sp,
          ),
          textAlign: TextAlign.center,
        ),
        if (data.comparisonText.isNotEmpty)
          Row(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              Icon(
                data.isPositive
                    ? Icons.trending_up_rounded
                    : Icons.trending_down_rounded,
                color: AppColors.white,
              ),
              6.szW,
              Flexible(
                child: AppText(
                  data.comparisonText,
                  style: AppTextStyles.bold13.copyWith(color: AppColors.white),
                  textAlign: TextAlign.center,
                ),
              ),
            ],
          ),
      ],
    ),
  );
}
