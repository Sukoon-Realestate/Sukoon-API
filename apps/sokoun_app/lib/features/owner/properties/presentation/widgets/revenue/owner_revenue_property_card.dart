part of '../../../imports.dart';

class OwnerRevenuePropertyCard extends StatelessWidget {
  const OwnerRevenuePropertyCard({super.key, required this.item});

  final OwnerRevenuePropertyContent item;

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: EdgeInsets.all(14.w),
      decoration: BoxDecoration(
        color: AppColors.white,
        borderRadius: BorderRadius.circular(17.r),
        border: Border.all(color: AppColors.sokoonBorder),
      ),
      child: Row(
        children: [
          Container(
            width: 44.r,
            height: 44.r,
            decoration: BoxDecoration(
              color: AppColors.grayBackground,
              borderRadius: BorderRadius.circular(13.r),
            ),
            child: Icon(
              Icons.apartment_rounded,
              color: AppColors.blueGray,
              size: 23.r,
            ),
          ),
          11.szW,
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.stretch,
              children: [
                AppText(
                  item.title,
                  color: AppColors.sokoonNavy,
                  fontSize: 13.sp,
                  fontWeight: FontWeight.w800,
                  maxLines: 1,
                  overflow: TextOverflow.ellipsis,
                ),
                5.szH,
                AppText(
                  item.dueDate,
                  color: AppColors.sokoonGray,
                  fontSize: 11.sp,
                ),
              ],
            ),
          ),
          10.szW,
          Column(
            crossAxisAlignment: CrossAxisAlignment.end,
            children: [
              AppText(
                '${_formatNumber(item.amount)} '
                '${LocaleKeys.ownerRevenueCurrency}',
                color: AppColors.sokoonNavy,
                fontSize: 14.sp,
                fontWeight: FontWeight.w800,
              ),
              5.szH,
              Container(
                padding: EdgeInsets.symmetric(horizontal: 8.w, vertical: 3.h),
                decoration: BoxDecoration(
                  color: item.status.backgroundColor,
                  borderRadius: BorderRadius.circular(99.r),
                ),
                child: AppText(
                  item.status.label,
                  color: item.status.foregroundColor,
                  fontSize: 10.sp,
                  fontWeight: FontWeight.w800,
                ),
              ),
            ],
          ),
        ],
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
