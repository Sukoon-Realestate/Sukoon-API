import 'package:flutter/material.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';
import 'package:melos_core/config/res/config_imports.dart';

class TenantPhotoNavButton extends StatelessWidget {
  const TenantPhotoNavButton({
    super.key,
    required this.icon,
    required this.onTap,
  });

  final IconData icon;
  final VoidCallback onTap;

  @override
  Widget build(BuildContext context) {
    return GestureDetector(
      onTap: onTap,
      behavior: HitTestBehavior.opaque,
      child: Container(
        width: 34.r,
        height: 34.r,
        alignment: Alignment.center,
        decoration: BoxDecoration(
          color: AppColors.blackAlpha35,
          borderRadius: BorderRadius.circular(12.r),
        ),
        child: Icon(icon, color: AppColors.white, size: 22.r),
      ),
    );
  }
}
