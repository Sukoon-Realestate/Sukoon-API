import 'package:flutter/material.dart';
import 'package:sokoun_app/shared_widgets/property_card_summary.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';
import 'package:melos_core/config/language/locale_keys.g.dart';
import 'package:melos_core/config/res/config_imports.dart';
import 'package:melos_core/core/extensions/align_helper.dart';
import 'package:melos_core/core/extensions/padding_extension.dart';
import 'package:melos_core/core/extensions/sized_box_helper.dart';
import 'package:melos_core/core/helpers/text_style_manager.dart';
import 'package:melos_core/core/navigation/navigator.dart';
import 'package:melos_core/core/widgets/app_text.dart';
import 'package:melos_core/core/widgets/image_widgets/cached_image.dart';
import 'package:sokoun_app/features/shared/rental_offers/presentation/widgets/rental_offer_labels.dart';
import 'package:sokoun_app/features/tenant/home/data/models/property_details_model.dart';
import 'favorite_offer_row.dart';
import 'package:sokoun_app/features/tenant/favorites/data/models/favorites_content.dart';
import 'package:sokoun_app/features/tenant/home/presentation/screens/property_details_screen.dart';
import 'package:sokoun_app/features/shared/rental_offers/data/enums/rental_listing_category.dart';
import 'package:sokoun_app/features/tenant/home/data/models/property_search_model.dart';

class FavoritePropertyCard extends StatelessWidget {
  const FavoritePropertyCard({
    super.key,
    required this.item,
    required this.onRemove,
    this.onOfferRemoved,
    this.category = RentalListingCategory.all,
  });

  final FavoritePropertyContent item;
  final VoidCallback onRemove;
  final VoidCallback? onOfferRemoved;
  final RentalListingCategory category;

  void _openProperty() {
    Go.to(
      PropertyDetailsScreen(
        propertyId: item.id,
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
      shape: RoundedRectangleBorder(
        borderRadius: BorderRadius.circular(16.r),
        side: BorderSide(color: context.appColor(AppColors.sokoonBorder)),
      ),
      clipBehavior: Clip.antiAlias,
      child: InkWell(
        onTap: item.id.isEmpty ? null : _openProperty,
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            _FavoritePropertyImage(
              onRemove: item.hasRentalOffers ? null : onRemove,
              imageUrl: item.mainImage,
            ),
            PropertyCardSummary(
              title: item.title,
              location: [
                item.district,
                item.city,
              ].where((value) => value.isNotEmpty).join(', '),
              metadata: _FavoritePropertyMeta(
                rating: item.ratingLabel,
                area: RentalOfferLabels.propertyArea(
                  item.area,
                  hasOffers: item.hasRentalOffers,
                ),
              ),
              tags: AppText(
                [
                  PropertyDetailsModel.propertyTypeLabelFor(item.propertyType),
                  if (item.savedOffers.isNotEmpty)
                    ...item.savedOffers
                        .map(
                          (offer) =>
                              offer.scope?.label ??
                              LocaleKeys.rentalCategoryUnspecified,
                        )
                        .toSet()
                  else
                    LocaleKeys.rentalCategoryUnspecified,
                ].join(' · '),
              ),
              price: RentalOfferLabels.savedListingPrice(
                item.savedOffers,
                hasInventory: item.hasRentalOffers,
                legacyPrice: item.price,
                legacyPeriod: item.pricePeriod,
              ),
            ).paddingSymmetric(horizontal: 16.w, vertical: 12.h),
            if (item.hasRentalOffers) ...[
              AppText(LocaleKeys.rentalSavedOffers).paddingAll(12),
              for (final offer in item.savedOffers)
                FavoriteOfferRow(
                  key: ValueKey(offer.offerId),
                  propertyId: item.id,
                  offer: offer,
                  onRemoved: onOfferRemoved,
                ),
              if (item.savedOffers.isEmpty)
                AppText(LocaleKeys.rentalSnapshotMissing).paddingAll(12),
            ],
          ],
        ),
      ),
    );
  }
}

class _FavoritePropertyImage extends StatelessWidget {
  const _FavoritePropertyImage({
    required this.onRemove,
    required this.imageUrl,
  });

  final VoidCallback? onRemove;
  final String imageUrl;

  @override
  Widget build(BuildContext context) {
    return AspectRatio(
      aspectRatio: 1.8,
      child: ColoredBox(
        color: context.appColor(AppColors.grayBluePale, surface: true),
        child: Stack(
          children: [
            Positioned.fill(
              child: imageUrl.isEmpty
                  ? _FavoriteImagePlaceholder()
                  : CachedImage(
                      url: imageUrl,
                      fit: BoxFit.cover,
                      placeHolder: const _FavoriteImagePlaceholder(),
                    ),
            ),
            if (onRemove != null)
              PositionedDirectional(
                top: 10.h,
                end: 10.w,
                child: Semantics(
                  button: true,
                  label: LocaleKeys.favoriteRemoveSemanticLabel,
                  child: GestureDetector(
                    onTap: onRemove,
                    behavior: HitTestBehavior.opaque,
                    child: Container(
                      width: 48.r,
                      height: 48.r,
                      alignment: Alignment.center,
                      decoration: BoxDecoration(
                        color: context
                            .appColor(AppColors.white, surface: true)
                            .withValues(alpha: .9),
                        shape: BoxShape.circle,
                      ),
                      child: Icon(
                        Icons.favorite_rounded,
                        color: context.appColor(AppColors.red),
                        size: 14.r,
                      ),
                    ),
                  ),
                ),
              ),
          ],
        ),
      ),
    );
  }
}

class _FavoriteImagePlaceholder extends StatelessWidget {
  const _FavoriteImagePlaceholder();

  @override
  Widget build(BuildContext context) {
    return ColoredBox(
      color: context.appColor(AppColors.grayBluePale, surface: true),
      child: Icon(
        Icons.apartment_rounded,
        color: AppColors.blueGrayLight,
        size: 28.r,
      ).centerWidget,
    );
  }
}

class _FavoritePropertyMeta extends StatelessWidget {
  const _FavoritePropertyMeta({required this.rating, required this.area});

  final String rating;
  final String area;

  @override
  Widget build(BuildContext context) {
    return Row(
      mainAxisSize: MainAxisSize.min,
      children: [
        Icon(
          Icons.star_rounded,
          color: context.appColor(AppColors.amber),
          size: 12.r,
        ),
        6.szW,
        AppText(
          rating,
          style: AppTextStyles.regular12.copyWith(
            color: context.appColor(AppColors.sokoonGray),
            fontSize: 12.sp,
            height: 1.45,
          ),
        ),
        if (area.isNotEmpty) ...[
          8.szW,
          AppText(
            '·',
            style: AppTextStyles.regular12.copyWith(
              color: context.appColor(AppColors.sokoonGray),
              fontSize: 12.sp,
              height: 1.45,
            ),
          ),
          8.szW,
          Flexible(
            child: AppText(
              area,
              style: AppTextStyles.regular12.copyWith(
                color: context.appColor(AppColors.sokoonGray),
                fontSize: 12.sp,
                height: 1.45,
              ),
            ),
          ),
        ],
      ],
    );
  }
}
