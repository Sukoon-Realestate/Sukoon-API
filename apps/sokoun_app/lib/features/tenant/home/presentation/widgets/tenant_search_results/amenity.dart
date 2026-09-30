import 'package:flutter/material.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';
import 'package:melos_core/config/res/config_imports.dart';
import 'package:melos_core/core/helpers/text_style_manager.dart';
import 'package:melos_core/core/widgets/app_text.dart';

class Amenity extends StatelessWidget {
  const Amenity({super.key, required this.icon, required this.label});

  final IconData icon;
  final String label;

  @override
  Widget build(BuildContext context) {
    return Row(
      mainAxisSize: MainAxisSize.min,
      spacing: 4.w,
      children: [
        Icon(icon, color: AppColors.sokoonGray, size: 15.r),
        AppText(
          label,
          style: AppTextStyles.regular12.copyWith(
            color: AppColors.sokoonGray,
            fontSize: 12.sp,
            height: 1.45,
          ),
        ),
      ],
    );
  }
}
