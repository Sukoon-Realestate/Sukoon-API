part of '../../imports.dart';

class OwnerRevenueScreen extends StatelessWidget {
  const OwnerRevenueScreen({super.key, this.properties, this.transactions});

  final List<OwnerRevenuePropertyContent>? properties;
  final List<OwnerTransactionContent>? transactions;

  @override
  Widget build(BuildContext context) {
    final List<OwnerRevenuePropertyContent> propertyItems =
        properties ?? OwnerRevenueContent.properties();
    final List<OwnerTransactionContent> transactionItems =
        transactions ?? OwnerRevenueContent.transactions();

    return Directionality(
      textDirection: TextDirection.rtl,
      child: Scaffold(
        backgroundColor: AppColors.scaffoldBackground,
        body: SafeArea(
          child: Column(
            children: [
              OwnerPropertyTopBar(
                title: LocaleKeys.ownerRevenueTitle,
                onBackPressed: () => Go.back(),
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
                            '21,500 ${LocaleKeys.ownerRevenueCurrency}',
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
                              LocaleKeys.ownerRevenueGrowth,
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
                    for (
                      int index = 0;
                      index < propertyItems.length;
                      index++
                    ) ...[
                      OwnerRevenuePropertyCard(item: propertyItems[index]),
                      if (index < propertyItems.length - 1) 10.szH,
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
                            index < transactionItems.length;
                            index++
                          ) ...[
                            OwnerTransactionRow(
                              transaction: transactionItems[index],
                            ),
                            if (index < transactionItems.length - 1)
                              Padding(
                                padding: EdgeInsets.symmetric(vertical: 13.h),
                                child: const Divider(
                                  height: 1,
                                  color: AppColors.sokoonBorder,
                                ),
                              ),
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
        bottomNavigationBar: const OwnerPropertiesBottomNavigation(
          activeTab: OwnerPropertiesNavigationTab.more,
        ),
      ),
    );
  }
}
