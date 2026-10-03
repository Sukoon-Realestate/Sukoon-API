import 'package:flutter/material.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';
import 'package:melos_core/config/res/config_imports.dart';
import 'package:melos_core/core/helpers/text_style_manager.dart';
import 'package:melos_core/core/widgets/app_text.dart';
import '../../data/models/public_page_content.dart';
import 'about_app_header.dart';

class PublicPageBody extends StatelessWidget {
  const PublicPageBody({
    super.key,
    required this.page,
    this.showAppIdentity = false,
  });
  final PublicPageContent page;
  final bool showAppIdentity;

  @override
  Widget build(BuildContext context) => SingleChildScrollView(
    padding: EdgeInsets.all(20.r),
    child: Column(
      crossAxisAlignment: CrossAxisAlignment.stretch,
      spacing: 16.h,
      children: [
        if (showAppIdentity) const AboutAppHeader(),
        AppText(
          page.title,
          style: AppTextStyles.bold.copyWith(
            fontSize: 20.sp,
            color: AppColors.sokoonNavy,
          ),
        ),
        SelectableText(
          page.content,
          textDirection: page.language == 'ar'
              ? TextDirection.rtl
              : page.language == 'en'
              ? TextDirection.ltr
              : null,
          style: AppTextStyles.regular14.copyWith(
            color: AppColors.sokoonNavy,
            height: 1.6,
          ),
        ),
      ],
    ),
  );
}
