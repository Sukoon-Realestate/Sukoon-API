import 'package:flutter/material.dart';
import 'package:melos_core/config/res/config_imports.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';

class HomeAvatar extends StatelessWidget {
  const HomeAvatar({
    super.key,
    required this.icon,
    required this.backgroundColor,
    required this.iconColor,
    this.imageUrl,
  });

  final IconData icon;
  final Color backgroundColor;
  final Color iconColor;
  final String? imageUrl;

  @override
  Widget build(BuildContext context) {
    return Container(
      width: 36.r,
      height: 36.r,
      decoration: BoxDecoration(
        color: context.appColor(backgroundColor, surface: true),
        shape: BoxShape.circle,
      ),
      child: imageUrl?.isNotEmpty ?? false
          ? ClipOval(
              child: Image.network(
                imageUrl!,
                fit: BoxFit.cover,
                errorBuilder: (context, error, stackTrace) =>
                    Icon(icon, color: context.appColor(iconColor), size: 18.r),
              ),
            )
          : Icon(icon, color: context.appColor(iconColor), size: 18.r),
    );
  }
}
