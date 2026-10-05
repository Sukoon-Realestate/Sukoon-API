import 'package:flutter/material.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';
import 'package:melos_core/config/res/config_imports.dart';
import 'package:melos_core/core/helpers/text_style_manager.dart';
import 'package:melos_core/core/widgets/app_text.dart';

class SearchSectionTitle extends StatelessWidget {
  const SearchSectionTitle(this.title, {super.key});

  final String title;

  @override
  Widget build(BuildContext context) {
    return AppText(
      title,
      style: AppTextStyles.bold13.copyWith(
        color: context.appColor(AppColors.sokoonGray),
        fontSize: 13.sp,
        height: 1.45,
      ),
      textAlign: TextAlign.start,
    );
  }
}
