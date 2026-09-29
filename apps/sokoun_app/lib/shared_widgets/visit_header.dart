import 'package:flutter/material.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';
import 'package:melos_core/config/res/config_imports.dart';
import 'package:melos_core/core/extensions/padding_extension.dart';
import 'package:melos_core/core/extensions/sized_box_helper.dart';
import 'package:melos_core/core/helpers/text_style_manager.dart';
import 'package:melos_core/core/navigation/navigator.dart';
import 'package:melos_core/core/widgets/app_text.dart';

class VisitHeader extends StatelessWidget {
  const VisitHeader({
    super.key,
    required this.title,
    this.isBackEnabled = true,
  });

  final String title;
  final bool isBackEnabled;

  @override
  Widget build(BuildContext context) {
    return SizedBox(
      height: 54.h,
      child: Row(
        children: [
          IconButton(
            onPressed: isBackEnabled ? Go.back : null,
            visualDensity: VisualDensity.compact,
            icon: Icon(
              Icons.arrow_back_ios_new_rounded,
              color: AppColors.sokoonNavy,
              size: 20.r,
            ),
          ),
          4.szW,
          Expanded(
            child: AppText(
              title,
              style: AppTextStyles.black20.copyWith(
                color: AppColors.sokoonNavy,
                fontSize: 20.sp,
                height: 1.45,
              ),
              maxLines: 1,
              overflow: TextOverflow.ellipsis,
            ),
          ),
        ],
      ).paddingSymmetric(horizontal: 14.w),
    );
  }
}
