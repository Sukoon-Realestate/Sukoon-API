part of '../../../imports.dart';

class OwnerTransactionRow extends StatelessWidget {
  const OwnerTransactionRow({super.key, required this.transaction});

  final OwnerTransactionContent transaction;

  @override
  Widget build(BuildContext context) {
    final Color amountColor = transaction.isCredit
        ? context.appColor(AppColors.green)
        : context.appColor(AppColors.red);
    final String sign = transaction.isCredit ? '+' : '-';

    return Row(
      children: [
        Container(
          width: 40.r,
          height: 40.r,
          decoration: BoxDecoration(
            color: transaction.isCredit
                ? context.appColor(AppColors.greenPale, surface: true)
                : context.appColor(AppColors.redPale, surface: true),
            borderRadius: BorderRadius.circular(12.r),
          ),
          child: Icon(
            transaction.isCredit
                ? Icons.south_west_rounded
                : Icons.north_east_rounded,
            color: context.appColor(amountColor),
            size: 20.r,
          ),
        ),
        11.szW,
        Expanded(
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.stretch,
            spacing: 3.h,
            children: [
              AppText(
                transaction.title,
                style: AppTextStyles.extraBold13.copyWith(
                  color: context.appColor(AppColors.sokoonNavy),
                  fontSize: 13.sp,
                  height: 1.45,
                ),
              ),
              AppText(
                transaction.date,
                style: AppTextStyles.regular11.copyWith(
                  color: context.appColor(AppColors.sokoonMuted),
                  fontSize: 11.sp,
                  height: 1.45,
                ),
              ),
              if (transaction.rentalSelection != null)
                AppText(
                  RentalOfferLabels.accommodation(transaction.rentalSelection!),
                ),
            ],
          ),
        ),
        AppText(
          '$sign${EgyptianPoundText.format(transaction.amount.abs())}',
          style: AppTextStyles.bold13.copyWith(
            color: context.appColor(amountColor),
            fontSize: 13.sp,
            height: 1.45,
          ),
        ),
      ],
    );
  }
}
