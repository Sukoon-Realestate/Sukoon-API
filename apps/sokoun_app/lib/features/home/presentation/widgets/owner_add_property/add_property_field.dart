import 'package:flutter/material.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';
import 'package:melos_core/config/res/config_imports.dart';
import 'package:melos_core/core/extensions/sized_box_helper.dart';
import 'package:melos_core/core/widgets/app_text.dart';
import 'package:sokoun_app/features/home/data/models/owner_add_property_content.dart';

class AddPropertyField extends StatelessWidget {
  const AddPropertyField({super.key, required this.field, this.suffix});

  final AddPropertyFieldContent field;
  final Widget? suffix;

  @override
  Widget build(BuildContext context) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.stretch,
      children: [
        AppText(
          field.label,
          color: AppColors.sokoonGray,
          fontSize: 12.sp,
          fontWeight: FontWeight.w600,
          textAlign: TextAlign.right,
        ),
        6.szH,
        Container(
          height: 46.h,
          padding: EdgeInsets.symmetric(horizontal: 14.w),
          decoration: BoxDecoration(
            color: field.isFocused ? AppColors.white : AppColors.grayOffWhite,
            borderRadius: BorderRadius.circular(12.r),
            border: Border.all(
              color: field.isFocused
                  ? AppColors.sokoonTeal
                  : AppColors.grayPale,
              width: field.isFocused ? 1.2 : 1,
            ),
          ),
          child: Row(
            textDirection: TextDirection.ltr,
            children: [
              if (suffix != null) ...[suffix!, 8.szW],
              Expanded(
                child: AppText(
                  field.value,
                  color: field.isFocused
                      ? AppColors.sokoonNavy
                      : AppColors.navyAlpha50,
                  fontSize: field.isFocused ? 16.sp : 13.sp,
                  fontWeight: field.isFocused
                      ? FontWeight.w900
                      : FontWeight.w400,
                  textAlign: field.textAlign,
                  maxLines: 1,
                  overflow: TextOverflow.ellipsis,
                ),
              ),
            ],
          ),
        ),
      ],
    );
  }
}
