import 'package:flutter/material.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';
import 'package:melos_core/config/res/config_imports.dart';
import 'package:melos_core/config/language/locale_keys.g.dart';
import 'package:melos_core/core/extensions/padding_extension.dart';
import 'package:melos_core/core/extensions/sized_box_helper.dart';
import 'package:melos_core/core/helpers/text_style_manager.dart';
import 'package:melos_core/core/widgets/app_text.dart';
import 'package:melos_core/core/widgets/image_widgets/cached_image.dart';

class TenantPropertyCard extends StatelessWidget {
  const TenantPropertyCard({
    super.key,
    required this.title,
    required this.rating,
    required this.area,
    required this.price,
    required this.icon,
    this.imageUrl,
    this.imageCount = 0,
  });

  final String title;
  final String rating;
  final String area;
  final String price;
  final IconData icon;
  final String? imageUrl;
  final int imageCount;

  @override
  Widget build(BuildContext context) {
    return Container(
      constraints: BoxConstraints(minHeight: 112.h),
      decoration: BoxDecoration(
        color: AppColors.white,
        borderRadius: BorderRadius.circular(16.r),
        border: Border.all(color: AppColors.sokoonBorder),
      ),
      clipBehavior: Clip.antiAlias,
      padding: EdgeInsetsDirectional.only(start: 10.w),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.center,
        children: [
          Container(
            width: 96.w,
            height: 96.h,
            clipBehavior: Clip.antiAlias,
            decoration: BoxDecoration(
              color: AppColors.grayBluePale,
              borderRadius: BorderRadius.circular(10.r),
            ),
            child: Stack(
              fit: StackFit.expand,
              children: [
                imageUrl != null && imageUrl!.isNotEmpty
                    ? CachedImage(
                        url: imageUrl!,
                        fit: BoxFit.cover,
                        width: 96.w,
                        height: 96.h,
                      )
                    : Icon(icon, color: AppColors.blueGrayLight, size: 26.r),
                if (imageCount > 0)
                  PositionedDirectional(
                    bottom: 6.h,
                    start: 6.w,
                    child: Semantics(
                      label:
                          '$imageCount ${LocaleKeys.tenantPropertyDetailsPhotoCountUnit}',
                      child: ExcludeSemantics(
                        child: Container(
                          padding: EdgeInsets.symmetric(
                            horizontal: 6.w,
                            vertical: 3.h,
                          ),
                          decoration: BoxDecoration(
                            color: AppColors.blackAlpha45,
                            borderRadius: BorderRadius.circular(8.r),
                          ),
                          child: Row(
                            mainAxisSize: MainAxisSize.min,
                            spacing: 4.w,
                            children: [
                              Icon(
                                Icons.photo_library_outlined,
                                color: AppColors.white,
                                size: 12.r,
                              ),
                              AppText(
                                '$imageCount',
                                style: AppTextStyles.medium11.copyWith(
                                  color: AppColors.white,
                                ),
                              ),
                            ],
                          ),
                        ),
                      ),
                    ),
                  ),
              ],
            ),
          ),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              mainAxisSize: MainAxisSize.min,
              children: [
                AppText(
                  title,
                  style: AppTextStyles.bold16.copyWith(
                    color: AppColors.sokoonNavy,
                    fontSize: 16.sp,
                    height: 1.45,
                  ),
                  maxLines: 2,
                  overflow: TextOverflow.ellipsis,
                ),
                6.szH,
                Row(
                  children: [
                    Icon(
                      Icons.star_rounded,
                      color: AppColors.amber,
                      size: 14.r,
                    ),
                    3.szW,
                    AppText(
                      rating,
                      style: AppTextStyles.regular12.copyWith(
                        color: AppColors.sokoonGray,
                        fontSize: 12.sp,
                        height: 1.45,
                      ),
                    ),
                    8.szW,
                    AppText(
                      '·',
                      style: AppTextStyles.regular12.copyWith(
                        color: AppColors.sokoonGray,
                        fontSize: 12.sp,
                        height: 1.45,
                      ),
                    ),
                    8.szW,
                    Expanded(
                      child: AppText(
                        area,
                        style: AppTextStyles.regular12.copyWith(
                          color: AppColors.sokoonGray,
                          fontSize: 12.sp,
                          height: 1.45,
                        ),
                        maxLines: 1,
                        overflow: TextOverflow.ellipsis,
                      ),
                    ),
                  ],
                ),
                12.szH,
                AppText(
                  price,
                  style: AppTextStyles.bold16.copyWith(
                    color: AppColors.sokoonTeal,
                    fontSize: 16.sp,
                    height: 1.45,
                  ),
                  maxLines: 1,
                  overflow: TextOverflow.ellipsis,
                ),
              ],
            ).paddingSymmetric(horizontal: 12.w, vertical: 11.h),
          ),
        ],
      ),
    );
  }
}
