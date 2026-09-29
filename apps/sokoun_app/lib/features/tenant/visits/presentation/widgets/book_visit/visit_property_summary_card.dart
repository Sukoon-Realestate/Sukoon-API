part of '../../../imports.dart';

class VisitPropertySummaryCard extends StatelessWidget {
  const VisitPropertySummaryCard({super.key, required this.property});

  final VisitPropertyContent property;

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: EdgeInsets.all(16.r),
      decoration: BoxDecoration(
        color: AppColors.white,
        borderRadius: BorderRadius.circular(18.r),
        border: Border.all(color: AppColors.sokoonBorder),
      ),
      child: Row(
        children: [
          Container(
            width: 42.r,
            height: 42.r,
            alignment: Alignment.center,
            decoration: BoxDecoration(
              color: AppColors.mintLight,
              borderRadius: BorderRadius.circular(12.r),
            ),
            child: Icon(
              Icons.apartment_rounded,
              color: AppColors.sokoonTeal,
              size: 19.r,
            ),
          ),
          12.szW,
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                AppText(
                  property.title,
                  style: AppTextStyles.bold14.copyWith(
                    color: AppColors.sokoonNavy,
                    fontSize: 14.sp,
                    height: 1.45,
                  ),
                  maxLines: 1,
                  overflow: TextOverflow.ellipsis,
                ),
                4.szH,
                AppText(
                  property.meta,
                  style: AppTextStyles.regular12.copyWith(
                    color: AppColors.sokoonGray,
                    fontSize: 12.sp,
                    height: 1.45,
                  ),
                  maxLines: 1,
                  overflow: TextOverflow.ellipsis,
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }
}
