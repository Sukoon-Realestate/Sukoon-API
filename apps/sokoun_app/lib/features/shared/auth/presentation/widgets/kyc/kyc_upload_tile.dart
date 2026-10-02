import 'dart:io';

import 'package:flutter/material.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';
import 'package:melos_core/config/language/locale_keys.g.dart';
import 'package:melos_core/config/res/config_imports.dart';
import 'package:melos_core/core/extensions/sized_box_helper.dart';
import 'package:melos_core/core/helpers/text_style_manager.dart';
import 'package:melos_core/core/helpers/validators.dart';
import 'package:melos_core/core/widgets/app_text.dart';

class KycUploadTile extends StatelessWidget {
  const KycUploadTile({
    super.key,
    required this.title,
    required this.onTap,
    this.fileName,
    this.image,
    this.emptyIcon = Icons.upload_file_outlined,
    this.emptyTitle,
    this.emptySubtitle,
  });

  final String title;
  final VoidCallback? onTap;
  final String? fileName;
  final File? image;
  final IconData emptyIcon;
  final String? emptyTitle;
  final String? emptySubtitle;

  bool get _isUploaded =>
      image != null || (fileName != null && fileName!.isNotEmpty);

  @override
  Widget build(BuildContext context) {
    final borderColor = _isUploaded ? AppColors.sokoonTeal : AppColors.grayPale;
    final backgroundColor = _isUploaded
        ? AppColors.tealAlpha03
        : AppColors.white;

    return Column(
      crossAxisAlignment: CrossAxisAlignment.stretch,
      spacing: 8.h,
      children: [
        AppText(
          title,
          style: AppTextStyles.extraBold.copyWith(
            color: AppColors.sokoonNavy,
            fontSize: 14.sp,
          ),
          maxLines: 1,
          overflow: TextOverflow.ellipsis,
        ),
        InkWell(
          onTap: onTap,
          borderRadius: BorderRadius.circular(14.r),
          child: Container(
            constraints: BoxConstraints(minHeight: 120.h),
            padding: EdgeInsets.all(12.r),
            decoration: BoxDecoration(
              color: backgroundColor,
              borderRadius: BorderRadius.circular(14.r),
              border: Border.all(color: borderColor, width: 1.2),
            ),
            alignment: Alignment.center,
            child: _isUploaded ? _UploadedContent(this) : _EmptyContent(this),
          ),
        ),
      ],
    );
  }
}

class _UploadedContent extends StatelessWidget {
  final KycUploadTile tile;

  const _UploadedContent(this.tile);

  @override
  Widget build(BuildContext context) {
    final File? image = tile.image;

    return Column(
      mainAxisSize: MainAxisSize.min,
      children: [
        if (image != null) ...[
          ClipRRect(
            borderRadius: BorderRadius.circular(10.r),
            child: Image.file(
              image,
              width: double.infinity,
              height: 118.h,
              fit: BoxFit.cover,
            ),
          ),
          10.szH,
        ] else
          Icon(
            Icons.check_circle_outline_rounded,
            color: AppColors.sokoonTeal,
            size: 28.r,
          ),
        Row(
          spacing: 8.w,
          children: [
            Icon(
              Icons.check_circle_outline_rounded,
              color: AppColors.sokoonTeal,
              size: 18.r,
            ),
            Expanded(
              child: AppText(
                tile.fileName ?? LocaleKeys.uploaded,
                style: AppTextStyles.bold12.copyWith(
                  color: AppColors.sokoonTeal,
                  fontSize: 12.sp,
                  height: 1.45,
                ),
                maxLines: 1,
                overflow: TextOverflow.ellipsis,
              ),
            ),
          ],
        ),
      ],
    );
  }
}

class _EmptyContent extends StatelessWidget {
  final KycUploadTile tile;

  const _EmptyContent(this.tile);

  @override
  Widget build(BuildContext context) {
    return Column(
      mainAxisSize: MainAxisSize.min,
      mainAxisAlignment: MainAxisAlignment.center,
      children: [
        Icon(tile.emptyIcon, color: AppColors.sokoonGray, size: 28.r),
        8.szH,
        AppText(
          tile.emptyTitle ?? LocaleKeys.tapToUpload,
          style: AppTextStyles.extraBold13.copyWith(
            color: AppColors.sokoonGray,
            fontSize: 13.sp,
            height: 1.45,
          ),
          textAlign: TextAlign.center,
          maxLines: 1,
          overflow: TextOverflow.ellipsis,
        ),
        5.szH,
        AppText(
          tile.emptySubtitle ?? Validators.accountDocumentUploadHint,
          style: AppTextStyles.regular11.copyWith(
            color: AppColors.sokoonMuted,
            fontSize: 11.sp,
            height: 1.45,
          ),
          textAlign: TextAlign.center,
          maxLines: 1,
          overflow: TextOverflow.ellipsis,
        ),
      ],
    );
  }
}
