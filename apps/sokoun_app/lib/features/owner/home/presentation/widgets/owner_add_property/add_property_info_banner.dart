import 'package:flutter/material.dart';
import 'package:sokoun_app/shared_widgets/sokoun_motion.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';
import 'package:melos_core/config/res/config_imports.dart';
import 'package:melos_core/core/extensions/sized_box_helper.dart';
import 'package:melos_core/core/widgets/app_text.dart';

class AddPropertyInfoBanner extends StatelessWidget {
  const AddPropertyInfoBanner({
    super.key,
    required this.text,
    this.title,
    this.backgroundColor = AppColors.mintPale,
    this.borderColor = AppColors.tealAlpha19,
    this.iconColor = AppColors.sokoonTeal,
    this.textColor = AppColors.sokoonNavy,
    this.icon = Icons.privacy_tip_outlined,
  });

  final String text;
  final String? title;
  final Color backgroundColor;
  final Color borderColor;
  final Color iconColor;
  final Color textColor;
  final IconData icon;

  @override
  Widget build(BuildContext context) {
    return AnimatedSize(
      duration: SokounMotion.duration(context, milliseconds: 240),
      curve: SokounMotion.curve,
      alignment: AlignmentDirectional.topStart,
      child: AnimatedContainer(
        duration: SokounMotion.duration(context, milliseconds: 240),
        padding: EdgeInsets.all(14.w),
        decoration: BoxDecoration(
          color: backgroundColor,
          borderRadius: BorderRadius.circular(14.r),
          border: Border.all(color: borderColor),
        ),
        child: Row(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Container(
              width: 34.r,
              height: 34.r,
              alignment: Alignment.center,
              decoration: BoxDecoration(
                color: AppColors.whiteAlpha50,
                borderRadius: BorderRadius.circular(10.r),
              ),
              child: Icon(icon, color: iconColor, size: 18.r),
            ),
            12.szW,
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  if (title != null) ...[
                    AppText(
                      title!,
                      color: AppColors.sokoonNavy,
                      fontSize: 12.sp,
                      fontWeight: FontWeight.w700,
                      maxLines: 1,
                      overflow: TextOverflow.ellipsis,
                    ),
                    3.szH,
                  ],
                  AppText(
                    text,
                    color: textColor,
                    fontSize: 12.sp,
                    fontWeight: title == null
                        ? FontWeight.w700
                        : FontWeight.w400,
                    maxLines: 2,
                    overflow: TextOverflow.ellipsis,
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
