import 'package:flutter/material.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';
import 'package:melos_core/config/language/locale_keys.g.dart';
import 'package:melos_core/config/res/config_imports.dart';
import 'package:melos_core/core/extensions/sized_box_helper.dart';
import 'package:melos_core/core/navigation/navigator.dart';
import 'package:melos_core/core/widgets/app_text.dart';
import 'package:melos_core/core/widgets/image_widgets/cached_image.dart';
import 'package:sokoun_app/features/tenant/favorites/data/models/favorites_content.dart';
import 'package:sokoun_app/shared_widgets/property_details_screen.dart';

class FavoritePropertyCard extends StatelessWidget {
  const FavoritePropertyCard({
    super.key,
    required this.item,
    required this.onRemove,
  });

  final FavoritePropertyContent item;
  final VoidCallback onRemove;

  @override
  Widget build(BuildContext context) {
    return GestureDetector(
      onTap: () => Go.to(PropertyDetailsScreen(propertyId: item.id)),
      child: Container(
        decoration: BoxDecoration(
          color: AppColors.white,
          borderRadius: BorderRadius.circular(24.r),
          border: Border.all(color: AppColors.sokoonBorder),
        ),
        clipBehavior: Clip.antiAlias,
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            _FavoritePropertyImage(
              onRemove: onRemove,
              itemId: item.id,
              imageUrl: item.mainImage,
            ),
            Padding(
              padding: EdgeInsets.symmetric(horizontal: 16.w, vertical: 12.h),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  AppText(
                    item.title,
                    color: AppColors.sokoonNavy,
                    fontSize: 14.sp,
                    fontWeight: FontWeight.w900,
                    maxLines: 1,
                    overflow: TextOverflow.ellipsis,
                  ),
                  4.szH,
                  Row(
                    textDirection: TextDirection.rtl,
                    children: [
                      Expanded(
                        child: _FavoritePropertyMeta(
                          rating: item.ratingLabel,
                          area: item.areaLabel,
                        ),
                      ),
                      8.szW,
                      Flexible(
                        child: AppText(
                          '${item.price} ${LocaleKeys.favoritesCurrencyShort}',
                          color: AppColors.sokoonTeal,
                          fontSize: 14.sp,
                          fontWeight: FontWeight.w900,
                          maxLines: 1,
                          overflow: TextOverflow.ellipsis,
                        ),
                      ),
                    ],
                  ),
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }
}

class _FavoritePropertyImage extends StatelessWidget {
  const _FavoritePropertyImage({
    required this.onRemove,
    required this.itemId,
    required this.imageUrl,
  });

  final VoidCallback onRemove;
  final String itemId;
  final String imageUrl;

  @override
  Widget build(BuildContext context) {
    return SizedBox(
      height: 128.h,
      child: ColoredBox(
        color: AppColors.grayBluePale,
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
            Positioned(
              top: 10.h,
              left: 10.w,
              child: Semantics(
                button: true,
                label: LocaleKeys.favoriteRemoveSemanticLabel,
                child: GestureDetector(
                  key: ValueKey('favorite-remove-$itemId'),
                  onTap: onRemove,
                  behavior: HitTestBehavior.opaque,
                  child: Container(
                    width: 32.r,
                    height: 32.r,
                    alignment: Alignment.center,
                    decoration: BoxDecoration(
                      color: AppColors.white.withValues(alpha: .9),
                      shape: BoxShape.circle,
                    ),
                    child: Icon(
                      Icons.favorite_rounded,
                      color: AppColors.red,
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
      color: AppColors.grayBluePale,
      child: Center(
        child: Icon(
          Icons.apartment_rounded,
          color: AppColors.blueGrayLight,
          size: 28.r,
        ),
      ),
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
      textDirection: TextDirection.rtl,
      children: [
        Icon(Icons.star_rounded, color: AppColors.amber, size: 12.r),
        6.szW,
        AppText(
          rating,
          color: AppColors.sokoonGray,
          fontSize: 12.sp,
          fontWeight: FontWeight.w400,
        ),
        8.szW,
        AppText(
          '·',
          color: AppColors.sokoonGray,
          fontSize: 12.sp,
          fontWeight: FontWeight.w400,
        ),
        8.szW,
        Flexible(
          child: AppText(
            area,
            color: AppColors.sokoonGray,
            fontSize: 12.sp,
            fontWeight: FontWeight.w400,
            maxLines: 1,
          ),
        ),
      ],
    );
  }
}
