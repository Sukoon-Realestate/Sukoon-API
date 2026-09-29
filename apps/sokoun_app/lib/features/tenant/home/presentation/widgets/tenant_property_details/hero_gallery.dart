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
    final int photoCount = imageUrls.length;
    final int thumbCount = imageUrls.length.clamp(0, 6);

    return Container(
      height: 258.h,
      decoration: const BoxDecoration(color: AppColors.grayBluePale),
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
              color: AppColors.blueGrayLight,
              size: 62.r,
            ).centerWidget,
          PositionedDirectional(
            top: 14.h,
            start: 14.w,
            end: 14.w,
            child: Row(
              children: [
                _HeroIconButton(
                  icon: Icons.arrow_back_ios_new_rounded,
                  tooltip: MaterialLocalizations.of(context).backButtonTooltip,
                  onPressed: Go.back,
                ),
                const Spacer(),
                _HeroIconButton(
                  icon: Icons.ios_share_rounded,
                  tooltip: LocaleKeys.tenantPropertyDetailsShare,
                  onPressed: () => _showShareSheet(context),
                ),
              ],
            ),
          ),
          PositionedDirectional(
            bottom: hasImages ? 76.h : 16.h,
            start: 14.w,
            end: 14.w,
            child: Wrap(
              spacing: 8.w,
              runSpacing: 8.h,
              children: [
                if (property.isVerified)
                  _HeroPill(
                    label: '${LocaleKeys.verified} ✓',
                    color: AppColors.sokoonTeal,
                    textColor: AppColors.white,
                  ),
                if (hasImages)
                  _HeroPill(
                    label:
                        '$photoCount ${LocaleKeys.tenantPropertyDetailsPhotoCountUnit}',
                    color: AppColors.blackAlpha45,
                    textColor: AppColors.white,
                  ),
              ],
            ),
          ),
          if (hasImages)
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
                    const color = AppColors.slate;
                    final bool showMoreOverlay =
                        index == thumbCount - 1 &&
                        imageUrls.length > thumbCount;
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
                                '+${imageUrls.length - thumbCount}',
                                color: AppColors.white,
                                fontSize: 11.sp,
                                fontWeight: FontWeight.w700,
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
    required this.icon,
    required this.tooltip,
    required this.onPressed,
  });

  final String tooltip;

  final IconData icon;
  final VoidCallback onPressed;

  @override
  Widget build(BuildContext context) {
    return IconButton.filled(
      tooltip: tooltip,
      onPressed: onPressed,
      style: IconButton.styleFrom(
        backgroundColor: AppColors.blackAlpha45,
        foregroundColor: AppColors.white,
        minimumSize: const Size(48, 48),
      ),
      icon: Icon(icon, size: 20.r),
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
