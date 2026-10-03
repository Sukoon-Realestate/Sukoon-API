part of '../../../imports.dart';

class OwnerPropertyCard extends StatelessWidget {
  const OwnerPropertyCard({
    super.key,
    required this.property,
    required this.onEditPressed,
    required this.onRejectedPressed,
  });

  final OwnerPropertyContent property;
  final VoidCallback onEditPressed;
  final VoidCallback onRejectedPressed;

  void _openProperty() {
    if (property.status.isRejected) {
      onRejectedPressed();
      return;
    }

    Go.to(PropertyDetailsScreen(propertyId: property.id));
  }

  @override
  Widget build(BuildContext context) {
    return Material(
      color: AppColors.white,
      borderRadius: BorderRadius.circular(20.r),
      child: InkWell(
        onTap: _openProperty,
        borderRadius: BorderRadius.circular(20.r),
        child: Container(
          padding: EdgeInsets.all(16.w),
          decoration: BoxDecoration(
            borderRadius: BorderRadius.circular(20.r),
            border: Border.all(color: AppColors.sokoonBorder),
            boxShadow: const [
              BoxShadow(
                color: AppColors.shadowBlack04,
                blurRadius: 4,
                offset: Offset(0, 2),
              ),
            ],
          ),
          child: Column(
            spacing: 14.h,
            children: [
              Row(
                crossAxisAlignment: CrossAxisAlignment.start,
                spacing: 12.w,
                children: [
                  Container(
                    width: 80.r,
                    height: 80.r,
                    decoration: BoxDecoration(
                      color: AppColors.grayBluePale,
                      borderRadius: BorderRadius.circular(16.r),
                    ),
                    child: property.mainImage.isEmpty
                        ? Icon(
                            Icons.apartment_rounded,
                            color: AppColors.blueGrayLight,
                            size: 30.r,
                          )
                        : CachedImage(
                            url: property.mainImage,
                            width: 80.r,
                            height: 80.r,
                            fit: BoxFit.cover,
                            borderRadius: BorderRadius.circular(16.r),
                            placeHolder: Icon(
                              Icons.apartment_rounded,
                              color: AppColors.blueGrayLight,
                              size: 30.r,
                            ),
                          ),
                  ),
                  Expanded(
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.end,
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
                          textAlign: TextAlign.start,
                        ),
                        6.szH,
                        OwnerPropertyStatusBadge(status: property.status),
                        8.szH,
                        AppText(
                          EgyptianPoundText.format(
                            property.monthlyPrice,
                            period: property.pricePeriod,
                          ),
                          style: AppTextStyles.bold16.copyWith(
                            color: AppColors.sokoonTeal,
                            fontSize: 16.sp,
                            height: 1.45,
                          ),
                          textAlign: TextAlign.start,
                        ),
                        6.szH,
                        AppText(
                          '${property.views} ${LocaleKeys.ownerPropertiesViewUnit}'
                          ' · ${property.visitRequests} ${LocaleKeys.ownerPropertiesVisitUnit}',
                          style: AppTextStyles.regular12.copyWith(
                            color: AppColors.sokoonGray,
                            fontSize: 12.sp,
                            height: 1.45,
                          ),
                          textAlign: TextAlign.start,
                        ),
                      ],
                    ),
                  ),
                ],
              ),
              Wrap(
                spacing: 8.w,
                runSpacing: 8.h,
                children: [
                  _OwnerPropertyCardAction(
                    label: LocaleKeys.ownerPropertiesEdit,
                    foregroundColor: AppColors.blue,
                    backgroundColor: AppColors.bluePale,
                    onPressed: onEditPressed,
                  ),
                  _OwnerPropertyCardAction(
                    label: LocaleKeys.ownerAnalyticsTitle,
                    foregroundColor: AppColors.sokoonTeal,
                    backgroundColor: AppColors.mintLight,
                    onPressed: () =>
                        Go.to(OwnerPropertyAnalyticsScreen(property: property)),
                  ),
                  _OwnerPropertyCardAction(
                    label: LocaleKeys.ownerAvailabilityTitle,
                    foregroundColor: AppColors.sokoonTeal,
                    backgroundColor: AppColors.mintLight,
                    onPressed: () => Go.to(
                      OwnerAvailabilityScreen(
                        ownerPropertyId: property.id,
                        availabilityStartDate: TimeZoneHelper.inLocation(
                          'Africa/Cairo',
                        ),
                      ),
                    ),
                  ),
                ],
              ),
            ],
          ),
        ),
      ),
    );
  }
}

class _OwnerPropertyCardAction extends StatelessWidget {
  const _OwnerPropertyCardAction({
    required this.label,
    required this.foregroundColor,
    required this.backgroundColor,
    required this.onPressed,
  });

  final String label;
  final Color foregroundColor;
  final Color backgroundColor;
  final VoidCallback onPressed;

  @override
  Widget build(BuildContext context) {
    return Material(
      color: backgroundColor,
      borderRadius: BorderRadius.circular(12.r),
      child: InkWell(
        onTap: onPressed,
        borderRadius: BorderRadius.circular(12.r),
        child: Padding(
          padding: EdgeInsets.symmetric(horizontal: 12.w, vertical: 14.h),
          child: AppText(
            label,
            style: AppTextStyles.bold12.copyWith(
              color: foregroundColor,
              fontSize: 12.sp,
              height: 1.45,
            ),
          ),
        ),
      ),
    );
  }
}
