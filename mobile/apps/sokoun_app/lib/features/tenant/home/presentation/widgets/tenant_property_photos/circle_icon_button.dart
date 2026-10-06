import 'package:flutter/material.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';
import 'package:melos_core/config/res/config_imports.dart';

class TenantPhotoCircleIconButton extends StatelessWidget {
  const TenantPhotoCircleIconButton({
    super.key,
    required this.icon,
    required this.onTap,
    required this.tooltip,
  });

  final IconData icon;
  final VoidCallback onTap;
  final String tooltip;

  @override
  Widget build(BuildContext context) {
    return IconButton.filled(
      tooltip: tooltip,
      onPressed: onTap,
      style: IconButton.styleFrom(
        minimumSize: Size.square(48.r),
        backgroundColor: AppColors.whiteAlpha10,
        foregroundColor: AppColors.white,
      ),
      icon: Icon(icon, size: 19.r),
    );
  }
}
