import 'package:flutter/material.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';
import 'package:melos_core/config/res/config_imports.dart';
import 'package:melos_core/core/widgets/app_text.dart';

class VisitSectionTitle extends StatelessWidget {
  const VisitSectionTitle(this.title, {super.key});

  final String title;

  @override
  Widget build(BuildContext context) {
    return AppText(
      title,
      color: AppColors.sokoonNavy,
      fontSize: 15.sp,
      fontWeight: FontWeight.w900,
      textAlign: TextAlign.right,
    );
  }
}
