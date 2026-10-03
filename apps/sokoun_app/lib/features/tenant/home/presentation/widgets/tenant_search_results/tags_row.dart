import 'package:flutter/material.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';
import 'package:melos_core/config/res/config_imports.dart';
import 'package:melos_core/core/helpers/text_style_manager.dart';
import 'package:melos_core/core/widgets/app_text.dart';

class TagsRow extends StatelessWidget {
  const TagsRow({super.key, required this.tags});

  final List<String> tags;

  @override
  Widget build(BuildContext context) {
    return Wrap(
      spacing: 6.w,
      runSpacing: 6.h,
      children: [
        for (final tag in tags)
          Container(
            padding: EdgeInsets.symmetric(horizontal: 9.w, vertical: 4.h),
            decoration: BoxDecoration(
              color: AppColors.grayBackground,
              borderRadius: BorderRadius.circular(999.r),
            ),
            child: AppText(
              tag,
              style: AppTextStyles.semiBold.copyWith(
                color: AppColors.sokoonGray,
                fontSize: 12.sp,
              ),
            ),
          ),
      ],
    );
  }
}
