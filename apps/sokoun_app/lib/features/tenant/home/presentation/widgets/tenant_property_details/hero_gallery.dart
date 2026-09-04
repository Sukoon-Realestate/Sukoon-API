import 'package:flutter/material.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';
import 'package:melos_core/config/language/locale_keys.g.dart';
import 'package:melos_core/config/res/config_imports.dart';
import 'package:melos_core/core/extensions/align_helper.dart';
import 'package:melos_core/core/extensions/sized_box_helper.dart';
import 'package:melos_core/core/navigation/navigator.dart';
import 'package:melos_core/core/widgets/app_text.dart';
import 'package:melos_core/core/widgets/image_widgets/cached_image.dart';
import 'package:sokoun_app/features/tenant/home/data/models/tenant_property_content.dart';
import 'package:sokoun_app/features/tenant/home/presentation/screens/tenant_property_photos_screen.dart';

import 'share_sheet.dart';

class TenantPropertyHeroGallery extends StatelessWidget {
  const TenantPropertyHeroGallery({super.key, required this.property});

  final TenantPropertyDetailsContent property;

  void _openPhotos(int index) {
    Go.to(TenantPropertyPhotosScreen(property: property, initialIndex: index));
  }

  void _showShareSheet(BuildContext context) {
    showModalBottomSheet<void>(
      context: context,
      backgroundColor: AppColors.transparent,
      builder: (_) => TenantPropertyShareSheet(shareUrl: property.shareUrl),
    );
  }

  @override
  Widget build(BuildContext context) {
    final List<String> imageUrls = property.imageUrls;
    final bool hasImages = imageUrls.isNotEmpty;
    final int photoCount = hasImages
        ? imageUrls.length
        : property.photoLabels.length + 3;
    final int thumbCount = hasImages && imageUrls.length < 6
        ? imageUrls.length
        : 6;

    return Container(
      height: 258.h,
      decoration: const BoxDecoration(
        gradient: LinearGradient(
          begin: AlignmentDirectional.topStart,
          end: AlignmentDirectional.bottomEnd,
          colors: [AppColors.tealDark, AppColors.sokoonTeal],
        ),
      ),
      child: Stack(
        children: [
          if (hasImages)
            Positioned.fill(
              child: CachedImage(
                url: imageUrls.first,
                fit: BoxFit.cover,
                height: 258.h,
              ),
            )
          else
            Icon(
              Icons.apartment_outlined,
              color: AppColors.whiteAlpha40,
              size: 62.r,
            ).centerWidget,
          PositionedDirectional(
            top: 14.h,
            start: 14.w,
            end: 14.w,
            child: Row(
              textDirection: TextDirection.ltr,
              children: [
                _HeroIconButton(
                  key: const ValueKey('tenant-property-details-back'),
                  icon: Icons.arrow_back_ios_new_rounded,
                  onPressed: Go.back,
                ),
                const Spacer(),
                _HeroIconButton(
                  key: const ValueKey('tenant-property-details-share'),
                  icon: Icons.ios_share_rounded,
                  onPressed: () => _showShareSheet(context),
                ),
              ],
            ),
          ),
          PositionedDirectional(
            bottom: 76.h,
            start: 14.w,
            child: Row(
              children: [
                if (property.isVerified)
                  _HeroPill(
                    label: '${LocaleKeys.verified} ✓',
                    color: AppColors.sokoonTeal,
                    textColor: AppColors.white,
                  ),
                8.szW,
                _HeroPill(
                  label:
                      '$photoCount ${LocaleKeys.tenantPropertyDetailsPhotoCountUnit}',
                  color: AppColors.blackAlpha45,
                  textColor: AppColors.white,
                ),
              ],
            ),
          ),
          PositionedDirectional(
            bottom: 0,
            start: 0,
            end: 0,
            child: Container(
              height: 64.h,
              color: AppColors.slate,
              padding: EdgeInsets.symmetric(horizontal: 12.w, vertical: 8.h),
              child: ListView.separated(
                scrollDirection: Axis.horizontal,
                reverse: true,
                itemBuilder: (context, index) {
                  final color =
                      property.imageColors[index % property.imageColors.length];
                  final bool showMoreOverlay = hasImages
                      ? index == thumbCount - 1 && imageUrls.length > thumbCount
                      : index == 5;
                  return GestureDetector(
                    onTap: () => _openPhotos(index),
                    behavior: HitTestBehavior.opaque,
                    child: Container(
                      width: index == 0 ? 64.w : 58.w,
                      decoration: BoxDecoration(
                        color: color,
                        borderRadius: BorderRadius.circular(10.r),
                        border: index == 0
                            ? Border.all(color: AppColors.white, width: 2)
                            : null,
                      ),
                      clipBehavior: Clip.antiAlias,
                      child: showMoreOverlay
                          ? AppText(
                              hasImages
                                  ? '+${imageUrls.length - thumbCount}\n${LocaleKeys.tenantPropertyDetailsPhotos}'
                                  : '+7\n${LocaleKeys.tenantPropertyDetailsPhotos}',
                              color: AppColors.white,
                              fontSize: 11.sp,
                              fontWeight: FontWeight.w900,
                              textAlign: TextAlign.center,
                            ).centerWidget
                          : hasImages
                          ? CachedImage(
                              url: imageUrls[index],
                              fit: BoxFit.cover,
                              width: index == 0 ? 64.w : 58.w,
                              height: 48.h,
                            )
                          : null,
                    ),
                  );
                },
                separatorBuilder: (context, index) => 8.szW,
                itemCount: thumbCount,
              ),
            ),
          ),
        ],
      ),
    );
  }
}

class _HeroIconButton extends StatelessWidget {
  const _HeroIconButton({
    super.key,
    required this.icon,
    required this.onPressed,
  });

  final IconData icon;
  final VoidCallback onPressed;

  @override
  Widget build(BuildContext context) {
    return GestureDetector(
      onTap: onPressed,
      behavior: HitTestBehavior.opaque,
      child: Container(
        width: 36.r,
        height: 36.r,
        alignment: Alignment.center,
        decoration: BoxDecoration(
          color: AppColors.blackAlpha35,
          borderRadius: BorderRadius.circular(18.r),
        ),
        child: Icon(icon, color: AppColors.white, size: 18.r),
      ),
    );
  }
}

class _HeroPill extends StatelessWidget {
  const _HeroPill({
    required this.label,
    required this.color,
    required this.textColor,
  });

  final String label;
  final Color color;
  final Color textColor;

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: EdgeInsets.symmetric(horizontal: 10.w, vertical: 5.h),
      decoration: BoxDecoration(
        color: color,
        borderRadius: BorderRadius.circular(8.r),
      ),
      child: AppText(
        label,
        color: textColor,
        fontSize: 11.sp,
        fontWeight: FontWeight.w800,
      ),
    );
  }
}
