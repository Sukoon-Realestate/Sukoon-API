import 'package:flutter/material.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';
import 'package:melos_core/config/res/config_imports.dart';

class TenantPhotoNavButton extends StatelessWidget {
  const TenantPhotoNavButton({
    super.key,
    required this.icon,
    required this.onTap,
    required this.tooltip,
  });

  final IconData icon;
  final VoidCallback? onTap;
  final String tooltip;

  @override
  Widget build(BuildContext context) {
    return IconButton.filled(
      tooltip: tooltip,
      onPressed: onTap,
      style: IconButton.styleFrom(
        minimumSize: Size.square(48.r),
        backgroundColor: AppColors.blackAlpha35,
        disabledBackgroundColor: AppColors.blackAlpha35,
        foregroundColor: AppColors.white,
        disabledForegroundColor: AppColors.whiteAlpha40,
      ),
      icon: Icon(icon, size: 22.r),
    );
  }
}
