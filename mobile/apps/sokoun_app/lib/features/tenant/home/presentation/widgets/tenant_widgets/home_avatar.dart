import 'package:flutter/material.dart';
import 'package:melos_core/config/res/config_imports.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';

class HomeAvatar extends StatelessWidget {
  const HomeAvatar({
    super.key,
    required this.icon,
    required this.backgroundColor,
    required this.iconColor,
  });

  final IconData icon;
  final Color backgroundColor;
  final Color iconColor;

  @override
  Widget build(BuildContext context) {
    return Container(
      width: 36.r,
      height: 36.r,
      decoration: BoxDecoration(
        color: context.appColor(backgroundColor, surface: true),
        shape: BoxShape.circle,
      ),
      child: Icon(icon, color: context.appColor(iconColor), size: 18.r),
    );
  }
}
