import 'package:flutter/material.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';
import 'package:melos_core/config/res/config_imports.dart';

class TenantPhotoCircleIconButton extends StatelessWidget {
  const TenantPhotoCircleIconButton({
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
        width: 36.r,
        height: 36.r,
        alignment: Alignment.center,
        decoration: const BoxDecoration(
          color: AppColors.whiteAlpha10,
          shape: BoxShape.circle,
        ),
        child: Icon(icon, color: AppColors.white, size: 19.r),
      ),
    );
  }
}
