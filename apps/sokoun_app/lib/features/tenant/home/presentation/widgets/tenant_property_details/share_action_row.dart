import 'package:flutter/material.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';
import 'package:melos_core/config/res/config_imports.dart';
import 'package:melos_core/core/extensions/sized_box_helper.dart';
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
          color: AppColors.white,
          borderRadius: BorderRadius.circular(14.r),
          border: Border.all(color: AppColors.grayPale),
        ),
        child: Row(
          children: [
            Container(
              width: 38.r,
              height: 38.r,
              alignment: Alignment.center,
              decoration: BoxDecoration(
                color: AppColors.grayBackground,
                borderRadius: BorderRadius.circular(12.r),
              ),
              child: Icon(icon, color: color, size: 18.r),
            ),
            12.szW,
            AppText(
              label,
              color: color,
              fontSize: 14.sp,
              fontWeight: FontWeight.w800,
            ),
          ],
        ),
      ),
    );
  }
}
