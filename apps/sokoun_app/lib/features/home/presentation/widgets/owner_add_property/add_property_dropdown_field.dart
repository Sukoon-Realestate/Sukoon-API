import 'package:flutter/material.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';
import 'package:melos_core/config/res/config_imports.dart';
import 'package:melos_core/core/extensions/sized_box_helper.dart';
import 'package:melos_core/core/widgets/app_text.dart';

class AddPropertyDropdownField extends StatelessWidget {
  const AddPropertyDropdownField({
    super.key,
    required this.label,
    required this.value,
    required this.items,
    required this.onChanged,
  });

  final String label;
  final String value;
  final List<String> items;
  final ValueChanged<String> onChanged;

  @override
  Widget build(BuildContext context) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.stretch,
      children: [
        AppText(
          label,
          color: AppColors.sokoonGray,
          fontSize: 12.sp,
          fontWeight: FontWeight.w600,
          textAlign: TextAlign.right,
        ),
        6.szH,
        Container(
          height: 46.h,
          padding: EdgeInsets.symmetric(horizontal: 12.w),
          decoration: BoxDecoration(
            color: AppColors.white,
            borderRadius: BorderRadius.circular(12.r),
            border: Border.all(color: AppColors.sokoonTeal, width: 1.2),
          ),
          child: DropdownButtonHideUnderline(
            child: DropdownButton<String>(
              value: value,
              isExpanded: true,
              icon: Icon(
                Icons.keyboard_arrow_down_rounded,
                color: AppColors.sokoonTeal,
                size: 20.r,
              ),
              dropdownColor: AppColors.white,
              borderRadius: BorderRadius.circular(12.r),
              alignment: AlignmentDirectional.centerEnd,
              onChanged: (newValue) {
                if (newValue != null) {
                  onChanged(newValue);
                }
              },
              selectedItemBuilder: (context) {
                return [
                  for (final item in items)
                    Align(
                      alignment: AlignmentDirectional.centerEnd,
                      child: AppText(
                        item,
                        color: AppColors.sokoonTeal,
                        fontSize: 15.sp,
                        fontWeight: FontWeight.w900,
                        maxLines: 1,
                        overflow: TextOverflow.ellipsis,
                      ),
                    ),
                ];
              },
              items: [
                for (final item in items)
                  DropdownMenuItem<String>(
                    value: item,
                    alignment: AlignmentDirectional.centerEnd,
                    child: AppText(
                      item,
                      color: AppColors.sokoonNavy,
                      fontSize: 13.sp,
                      fontWeight: FontWeight.w700,
                      maxLines: 1,
                      overflow: TextOverflow.ellipsis,
                    ),
                  ),
              ],
            ),
          ),
        ),
      ],
    );
  }
}
