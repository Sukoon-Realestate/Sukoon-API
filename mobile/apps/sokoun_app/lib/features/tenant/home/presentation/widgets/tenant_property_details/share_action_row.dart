import 'package:flutter/material.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';
import 'package:melos_core/config/res/config_imports.dart';
import 'package:melos_core/core/helpers/text_style_manager.dart';
import 'package:melos_core/core/widgets/app_text.dart';

class TenantPropertyShareActionRow extends StatelessWidget {
  const TenantPropertyShareActionRow({
    super.key,
    required this.icon,
    required this.label,
    required this.color,
    required this.onActionPressed,
  });

  final IconData icon;
  final String label;
  final Color color;
  final VoidCallback onActionPressed;

  @override
  Widget build(BuildContext context) {
    return GestureDetector(
      onTap: onActionPressed,
      behavior: HitTestBehavior.opaque,
      child: Container(
        padding: EdgeInsets.all(14.w),
        decoration: BoxDecoration(
          color: context.appColor(AppColors.white, surface: true),
          borderRadius: BorderRadius.circular(14.r),
          border: Border.all(color: context.appColor(AppColors.grayPale)),
        ),
        child: Row(
          spacing: 12.w,
          children: [
            Container(
              width: 38.r,
              height: 38.r,
              alignment: Alignment.center,
              decoration: BoxDecoration(
                color: context.appColor(
                  AppColors.grayBackground,
                  surface: true,
                ),
                borderRadius: BorderRadius.circular(12.r),
              ),
              child: Icon(icon, color: context.appColor(color), size: 18.r),
            ),
            AppText(
              label,
              style: AppTextStyles.extraBold.copyWith(
                color: context.appColor(color),
                fontSize: 14.sp,
              ),
            ),
          ],
        ),
      ),
    );
  }
}
