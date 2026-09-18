part of '../../imports.dart';

class OwnerRevenueScreen extends StatelessWidget {
  const OwnerRevenueScreen({
    super.key,
    required this.properties,
    required this.transactions,
    required this.totalThisMonth,
    required this.growthLabel,
    this.showBackButton = true,
  });

  final List<OwnerRevenuePropertyContent> properties;
  final List<OwnerTransactionContent> transactions;
  final int totalThisMonth;
  final String growthLabel;
  final bool showBackButton;

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: AppColors.scaffoldBackground,
      body: SafeArea(
        child: Column(
          children: [
            OwnerPropertyTopBar(
              title: LocaleKeys.ownerRevenueTitle,
              showBackButton: showBackButton,
            ),
            Expanded(
              child: ListView(
                padding: EdgeInsets.fromLTRB(20.w, 4.h, 20.w, 24.h),
                children: [
                  Container(
                    padding: EdgeInsets.all(20.w),
                    decoration: BoxDecoration(
                      gradient: const LinearGradient(
                        colors: [AppColors.tealDeep, AppColors.sokoonTeal],
                      ),
                      borderRadius: BorderRadius.circular(22.r),
                    ),
                    child: Column(
                      children: [
                        AppText(
                          LocaleKeys.ownerRevenueThisMonth,
                          color: AppColors.whiteAlpha60,
                          fontSize: 13.sp,
                          fontWeight: FontWeight.w700,
                        ),
                        8.szH,
                        AppText(
                          '${_formatNumber(totalThisMonth)} ${LocaleKeys.ownerRevenueCurrency}',
                          color: AppColors.white,
                          fontSize: 30.sp,
                          fontWeight: FontWeight.w900,
                        ),
                        8.szH,
                        Container(
                          padding: EdgeInsets.symmetric(
                            horizontal: 10.w,
                            vertical: 5.h,
                          ),
                          decoration: BoxDecoration(
                            color: AppColors.whiteAlpha10,
                            borderRadius: BorderRadius.circular(99.r),
                          ),
                          child: AppText(
                            growthLabel,
                            color: AppColors.white,
                            fontSize: 11.sp,
                            fontWeight: FontWeight.w700,
                          ),
                        ),
                      ],
                    ),
                  ),
                  22.szH,
                  AppText(
                    LocaleKeys.ownerRevenueProperties,
                    color: AppColors.sokoonNavy,
                    fontSize: 16.sp,
                    fontWeight: FontWeight.w900,
                  ),
                  10.szH,
                  for (int index = 0; index < properties.length; index++) ...[
                    OwnerRevenuePropertyCard(item: properties[index]),
                    if (index < properties.length - 1) 10.szH,
                  ],
                  22.szH,
                  AppText(
                    LocaleKeys.ownerRevenueLatestTransactions,
                    color: AppColors.sokoonNavy,
                    fontSize: 16.sp,
                    fontWeight: FontWeight.w900,
                  ),
                  10.szH,
                  Container(
                    padding: EdgeInsets.all(16.w),
                    decoration: BoxDecoration(
                      color: AppColors.white,
                      borderRadius: BorderRadius.circular(18.r),
                      border: Border.all(color: AppColors.sokoonBorder),
                    ),
                    child: Column(
                      children: [
                        for (
                          int index = 0;
                          index < transactions.length;
                          index++
                        ) ...[
                          OwnerTransactionRow(transaction: transactions[index]),
                          if (index < transactions.length - 1)
                            const Divider(
                              height: 1,
                              color: AppColors.sokoonBorder,
                            ).paddingSymmetric(vertical: 13.h),
                        ],
                      ],
                    ),
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
