part of '../../../imports.dart';

class OwnerPropertyCard extends StatelessWidget {
  const OwnerPropertyCard({
    super.key,
    required this.property,
    required this.onEditPressed,
    required this.onRejectedPressed,
    required this.onDeletePressed,
    this.onInventoryChanged,
    this.onEditOfferPressed,
    this.category = RentalListingCategory.all,
  });

  final OwnerPropertyContent property;
  final VoidCallback onEditPressed;
  final VoidCallback onRejectedPressed;
  final VoidCallback onDeletePressed;
  final ValueChanged<PropertyDetailsModel>? onInventoryChanged;
  final ValueChanged<String>? onEditOfferPressed;
  final RentalListingCategory category;

  void _openProperty() {
    if (property.status.isRejected) {
      onRejectedPressed();
      return;
    }

    Go.to(
      PropertyDetailsScreen(
        propertyId: property.id,
        searchPreferences: PropertySearchFilters.initial(
          rentalScope: category.scope?.value ?? '',
        ),
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    return Material(
      color: context.appColor(AppColors.white, surface: true),
      borderRadius: BorderRadius.circular(20.r),
      child: InkWell(
        onTap: _openProperty,
        borderRadius: BorderRadius.circular(20.r),
        child: Container(
          padding: EdgeInsets.all(16.w),
          decoration: BoxDecoration(
            borderRadius: BorderRadius.circular(20.r),
            border: Border.all(color: context.appColor(AppColors.sokoonBorder)),
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
                      color: context.appColor(
                        AppColors.grayBluePale,
                        surface: true,
                      ),
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
                            color: context.appColor(AppColors.sokoonNavy),
                            fontSize: 14.sp,
                            height: 1.45,
                          ),
                          maxLines: 2,
                          overflow: TextOverflow.ellipsis,
                          textAlign: TextAlign.start,
                        ),
                        6.szH,
                        if (property.propertyType.isNotEmpty ||
                            property.location.isNotEmpty)
                          AppText(
                            [
                              PropertyDetailsModel.propertyTypeLabelFor(
                                property.propertyType,
                              ),
                              property.location,
                            ].where((part) => part.isNotEmpty).join(' · '),
                          ),
                        OwnerPropertyStatusBadge(status: property.status),
                        AppText(
                          category != RentalListingCategory.all
                              ? RentalListingCategories.label(category)
                              : property.rentalInventory != null
                              ? property.rentalInventory!.offers
                                    .map(
                                      (offer) =>
                                          offer.scope?.label ??
                                          LocaleKeys.rentalCategoryUnspecified,
                                    )
                                    .toSet()
                                    .join(' · ')
                              : property.rentalScopes.isNotEmpty
                              ? property.rentalScopes
                                    .map(
                                      (scope) =>
                                          RentalScope.fromValue(scope)?.label ??
                                          LocaleKeys.rentalCategoryUnspecified,
                                    )
                                    .join(' · ')
                              : RentalOfferLabels.listingFacts(
                                  property.rentalSummary,
                                ).join(' · '),
                        ),
                        8.szH,
                        AppText(
                          RentalOfferLabels.listingPrice(
                            property.rentalSummary,
                            hasInventory: property.hasRentalOffers,
                            legacyPrice: property.monthlyPrice.toString(),
                            legacyPeriod: property.pricePeriod,
                            contextScope: category.scope?.value ?? '',
                          ),
                          style: AppTextStyles.bold16.copyWith(
                            color: context.appColor(AppColors.sokoonTeal),
                            fontSize: 16.sp,
                            height: 1.45,
                          ),
                          textAlign: TextAlign.start,
                        ),
                        if (property.manageableOfferCount != null &&
                            property.hasRentalOffers)
                          AppText(
                            LocaleKeys.rentalManageableOfferCount.replaceAll(
                              '{count}',
                              '${property.manageableOfferCount}',
                            ),
                          ),
                        6.szH,
                        AppText(
                          '${property.views} ${LocaleKeys.ownerPropertiesViewUnit}'
                          ' · ${property.visitRequests} ${LocaleKeys.ownerPropertiesVisitUnit}',
                          style: AppTextStyles.regular12.copyWith(
                            color: context.appColor(AppColors.sokoonGray),
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
              if (property.rentalInventory != null)
                OwnerRentalOffersPanel(
                  propertyId: property.id,
                  inventory: property.rentalInventory!,
                  onConfirmed: onInventoryChanged,
                  onEditOffer: onEditOfferPressed,
                  category: category,
                ),
              Wrap(
                spacing: 8.w,
                runSpacing: 8.h,
                children: [
                  _OwnerPropertyCardAction(
                    label: property.rentalInventory == null
                        ? LocaleKeys.ownerPropertiesEdit
                        : LocaleKeys.rentalEditSharedProperty,
                    foregroundColor: context.appColor(AppColors.blue),
                    backgroundColor: context.appColor(
                      AppColors.bluePale,
                      surface: true,
                    ),
                    onPressed: onEditPressed,
                  ),
                  _OwnerPropertyCardAction(
                    label: LocaleKeys.ownerAnalyticsTitle,
                    foregroundColor: context.appColor(AppColors.sokoonTeal),
                    backgroundColor: context.appColor(
                      AppColors.mintLight,
                      surface: true,
                    ),
                    onPressed: () =>
                        Go.to(OwnerPropertyAnalyticsScreen(property: property)),
                  ),
                  _OwnerPropertyCardAction(
                    label: LocaleKeys.ownerPropertiesDeleteProperty,
                    foregroundColor: context.appColor(AppColors.red),
                    backgroundColor: context
                        .appColor(AppColors.red, surface: true)
                        .withValues(alpha: .2),
                    onPressed: onDeletePressed,
                  ),
                ],
              ),
              if (property.id.isNotEmpty)
                OwnerPropertyPremiumActions(property: property),
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
      color: context.appColor(backgroundColor, surface: true),
      borderRadius: BorderRadius.circular(12.r),
      child: InkWell(
        onTap: onPressed,
        borderRadius: BorderRadius.circular(12.r),
        child: Padding(
          padding: EdgeInsets.symmetric(horizontal: 12.w, vertical: 14.h),
          child: AppText(
            label,
            style: AppTextStyles.bold12.copyWith(
              color: context.appColor(foregroundColor),
              fontSize: 12.sp,
              height: 1.45,
            ),
          ),
        ),
      ),
    );
  }
}
