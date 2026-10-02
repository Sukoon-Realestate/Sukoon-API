import 'package:flutter/material.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';
import 'package:melos_core/config/res/config_imports.dart';
import 'package:melos_core/core/helpers/text_style_manager.dart';
import 'package:melos_core/core/widgets/app_text.dart';

class SokounCountBadge extends StatelessWidget {
  const SokounCountBadge({super.key, required this.count, required this.size});

  final int count;
  final double size;

  @override
  Widget build(BuildContext context) => Container(
    constraints: BoxConstraints(minWidth: size),
    height: size,
    alignment: Alignment.center,
    padding: EdgeInsets.symmetric(horizontal: 4.w),
    decoration: BoxDecoration(
      color: AppColors.red,
      borderRadius: BorderRadius.circular(size),
      border: Border.all(color: AppColors.white),
    ),
    child: AppText(
      count > 99 ? '99+' : '$count',
      style: AppTextStyles.extraBold.copyWith(
        color: AppColors.white,
        fontSize: 9.sp,
      ),
      maxLines: 1,
    ),
  );
}
