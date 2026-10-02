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
              spacing: 5.h,
              children: [
                AppText(
                  item.title,
                  style: AppTextStyles.extraBold13.copyWith(
                    color: AppColors.sokoonNavy,
                    fontSize: 13.sp,
                    height: 1.45,
                  ),
                  maxLines: 1,
                  overflow: TextOverflow.ellipsis,
                ),
                AppText(
                  item.dueDate,
                  style: AppTextStyles.regular11.copyWith(
                    color: AppColors.sokoonGray,
                    fontSize: 11.sp,
                    height: 1.45,
                  ),
                ),
              ],
            ),
          ),
          10.szW,
          Column(
            crossAxisAlignment: CrossAxisAlignment.end,
            spacing: 5.h,
            children: [
              AppText(
                '${item.amountLabel} ${item.currency}',
                style: AppTextStyles.extraBold.copyWith(
                  color: AppColors.sokoonNavy,
                  fontSize: 14.sp,
                ),
              ),
              Container(
                padding: EdgeInsets.symmetric(horizontal: 8.w, vertical: 3.h),
                decoration: BoxDecoration(
                  color: item.status.backgroundColor,
                  borderRadius: BorderRadius.circular(99.r),
                ),
                child: AppText(
                  item.statusLabel.isNotEmpty
                      ? item.statusLabel
                      : item.status.label,
                  style: AppTextStyles.extraBold.copyWith(
                    color: item.status.foregroundColor,
                    fontSize: 10.sp,
                  ),
                ),
              ),
            ],
          ),
        ],
      ),
    );
  }
}
