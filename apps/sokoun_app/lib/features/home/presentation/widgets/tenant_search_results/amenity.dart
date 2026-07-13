import 'package:flutter/material.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';
import 'package:melos_core/config/res/config_imports.dart';
import 'package:melos_core/core/extensions/sized_box_helper.dart';
import 'package:melos_core/core/widgets/app_text.dart';

class Amenity extends StatelessWidget {
  const Amenity({super.key, required this.icon, required this.label});

  final IconData icon;
  final String label;

  @override
  Widget build(BuildContext context) {
    return Row(
      mainAxisSize: MainAxisSize.min,
      children: [
        Icon(icon, color: AppColors.sokoonGray, size: 15.r),
        4.szW,
        AppText(
          label,
          color: AppColors.sokoonGray,
          fontSize: 12.sp,
          fontWeight: FontWeight.w400,
        ),
      ],
    );
  }
}
