part of '../../../imports.dart';

class OwnerTransactionRow extends StatelessWidget {
  const OwnerTransactionRow({super.key, required this.transaction});

  final OwnerTransactionContent transaction;

  @override
  Widget build(BuildContext context) {
    final Color amountColor = transaction.isCredit
        ? AppColors.green
        : AppColors.red;
    final String sign = transaction.isCredit ? '+' : '-';
    final int absoluteAmount = transaction.amount.abs();

    return Row(
      children: [
        Container(
          width: 40.r,
          height: 40.r,
          decoration: BoxDecoration(
            color: transaction.isCredit
                ? AppColors.greenPale
                : AppColors.redPale,
            borderRadius: BorderRadius.circular(12.r),
          ),
          child: Icon(
            transaction.isCredit
                ? Icons.south_west_rounded
                : Icons.north_east_rounded,
            color: amountColor,
            size: 20.r,
          ),
        ),
        11.szW,
        Expanded(
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: [
              AppText(
                transaction.title,
                color: AppColors.sokoonNavy,
                fontSize: 13.sp,
                fontWeight: FontWeight.w800,
              ),
              3.szH,
              AppText(
                transaction.date,
                color: AppColors.sokoonMuted,
                fontSize: 11.sp,
              ),
            ],
          ),
        ),
        AppText(
          '$sign${_formatNumber(absoluteAmount)} '
          '${LocaleKeys.ownerRevenueCurrency}',
          color: amountColor,
          fontSize: 13.sp,
          fontWeight: FontWeight.w700,
        ),
      ],
    );
  }

  String _formatNumber(int value) {
    return value.toString().replaceAllMapped(
      RegExp(r'(\d)(?=(\d{3})+(?!\d))'),
      (match) => '${match[1]},',
    );
  }
}
