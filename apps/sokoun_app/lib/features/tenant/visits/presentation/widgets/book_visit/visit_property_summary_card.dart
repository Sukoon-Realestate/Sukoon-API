part of '../../../imports.dart';

class VisitPropertySummaryCard extends StatelessWidget {
  const VisitPropertySummaryCard({super.key, required this.property});

  final VisitPropertyContent property;

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: EdgeInsets.all(16.r),
      decoration: BoxDecoration(
        color: context.appColor(AppColors.white, surface: true),
        borderRadius: BorderRadius.circular(18.r),
        border: Border.all(color: context.appColor(AppColors.sokoonBorder)),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          if (property.selection != null)
            RentalSelectionPanel(selection: property.selection!),
          if (property.hasRentalOffers) AppText(LocaleKeys.rentalViewingOnly),
          Row(
            spacing: 12.w,
            children: [
              Container(
                width: 42.r,
                height: 42.r,
                alignment: Alignment.center,
                decoration: BoxDecoration(
                  color: context.appColor(AppColors.mintLight, surface: true),
                  borderRadius: BorderRadius.circular(12.r),
                ),
                child: Icon(
                  Icons.apartment_rounded,
                  color: context.appColor(AppColors.sokoonTeal),
                  size: 19.r,
                ),
              ),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  spacing: 4.h,
                  children: [
                    AppText(
                      property.title,
                      style: AppTextStyles.bold14.copyWith(
                        color: context.appColor(AppColors.sokoonNavy),
                        fontSize: 14.sp,
                        height: 1.45,
                      ),
                      maxLines: 1,
                      overflow: TextOverflow.ellipsis,
                    ),
                    AppText(
                      property.meta,
                      style: AppTextStyles.regular12.copyWith(
                        color: context.appColor(AppColors.sokoonGray),
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
        ],
      ),
    );
  }
}
