import 'package:flutter/material.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';
import 'package:melos_core/config/language/locale_keys.g.dart';
import 'package:melos_core/config/res/config_imports.dart';
import 'package:melos_core/core/helpers/text_style_manager.dart';
import 'package:melos_core/core/widgets/app_text.dart';
import 'package:melos_core/core/widgets/image_widgets/cached_image.dart';
import 'package:sokoun_app/features/tenant/home/data/models/property_details_model.dart';

class ResultImageHeader extends StatelessWidget {
  const ResultImageHeader({super.key, required this.item});

  final PropertyDetailsModel item;

  @override
  Widget build(BuildContext context) {
    final int photoCount = item.imageUrls.length;
    return AspectRatio(
      aspectRatio: 1.8,
      child: Stack(
        children: [
          Positioned.fill(
            child: item.mainImage.isEmpty
                ? Container(
                    color: AppColors.tealMuted,
                    alignment: Alignment.center,
                    child: Icon(
                      Icons.image_outlined,
                      color: AppColors.whiteAlpha60,
                      size: 36.r,
                    ),
                  )
                : CachedImage(
                    url: item.mainImage,
                    fit: BoxFit.cover,
                    placeHolder: Icon(
                      Icons.image_outlined,
                      color: AppColors.whiteAlpha60,
                      size: 36.r,
                    ),
                  ),
          ),
          if (item.isVerified)
            PositionedDirectional(
              top: 10.h,
              end: 10.w,
              child: Container(
                padding: EdgeInsets.symmetric(horizontal: 8.w, vertical: 4.h),
                decoration: BoxDecoration(
                  color: AppColors.sokoonTeal,
                  borderRadius: BorderRadius.circular(7.r),
                ),
                child: AppText(
                  '${LocaleKeys.verified} ✓',
                  style: AppTextStyles.extraBold.copyWith(
                    color: AppColors.white,
                    fontSize: 12.sp,
                  ),
                ),
              ),
            ),
          PositionedDirectional(
            start: 10.w,
            bottom: 10.h,
            child: Container(
              padding: EdgeInsets.symmetric(horizontal: 8.w, vertical: 4.h),
              decoration: BoxDecoration(
                color: AppColors.blackAlpha45,
                borderRadius: BorderRadius.circular(7.r),
              ),
              child: AppText(
                '$photoCount ${LocaleKeys.chatPhotos}',
                style: AppTextStyles.semiBold.copyWith(
                  color: AppColors.white,
                  fontSize: 12.sp,
                ),
              ),
            ),
          ),
        ],
      ),
    );
  }
}
