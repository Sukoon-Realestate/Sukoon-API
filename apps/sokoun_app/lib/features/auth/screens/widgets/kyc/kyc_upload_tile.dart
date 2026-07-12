import 'package:flutter/material.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';
import 'package:melos_core/config/language/locale_keys.g.dart';
import 'package:melos_core/config/res/config_imports.dart';
import 'package:melos_core/core/extensions/sized_box_helper.dart';
import 'package:melos_core/core/widgets/app_text.dart';

class KycUploadTile extends StatelessWidget {
  const KycUploadTile({
    super.key,
    required this.title,
    required this.onTap,
    this.fileName,
    this.emptyIcon = Icons.upload_file_outlined,
    this.emptyTitle,
    this.emptySubtitle,
  });

  final String title;
  final VoidCallback? onTap;
  final String? fileName;
  final IconData emptyIcon;
  final String? emptyTitle;
  final String? emptySubtitle;

  bool get _isUploaded => fileName != null && fileName!.isNotEmpty;

  @override
  Widget build(BuildContext context) {
    final borderColor = _isUploaded ? AppColors.sokoonTeal : AppColors.grayPale;
    final backgroundColor = _isUploaded
        ? AppColors.tealAlpha03
        : AppColors.white;

    return Column(
      crossAxisAlignment: CrossAxisAlignment.stretch,
      children: [
        AppText(
          title,
          color: AppColors.sokoonNavy,
          fontSize: 14.sp,
          fontWeight: FontWeight.w800,
          maxLines: 1,
          overflow: TextOverflow.ellipsis,
        ),
        8.szH,
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
            child: Column(
              mainAxisSize: MainAxisSize.min,
              mainAxisAlignment: MainAxisAlignment.center,
              children: [
                Icon(
                  _isUploaded ? Icons.check_circle_outline_rounded : emptyIcon,
                  color: _isUploaded
                      ? AppColors.sokoonTeal
                      : AppColors.sokoonGray,
                  size: 28.r,
                ),
                8.szH,
                AppText(
                  _isUploaded
                      ? LocaleKeys.uploaded
                      : emptyTitle ?? LocaleKeys.tapToUpload,
                  color: _isUploaded
                      ? AppColors.sokoonTeal
                      : AppColors.sokoonGray,
                  fontSize: 13.sp,
                  fontWeight: FontWeight.w800,
                  textAlign: TextAlign.center,
                  maxLines: 1,
                  overflow: TextOverflow.ellipsis,
                ),
                5.szH,
                AppText(
                  _isUploaded
                      ? fileName!
                      : emptySubtitle ?? LocaleKeys.jpgPngUpTo5mb,
                  color: _isUploaded
                      ? AppColors.sokoonTeal
                      : AppColors.sokoonMuted,
                  fontSize: 11.sp,
                  fontWeight: FontWeight.w400,
                  textAlign: TextAlign.center,
                  maxLines: 1,
                  overflow: TextOverflow.ellipsis,
                ),
              ],
            ),
          ),
        ),
      ],
    );
  }
}
