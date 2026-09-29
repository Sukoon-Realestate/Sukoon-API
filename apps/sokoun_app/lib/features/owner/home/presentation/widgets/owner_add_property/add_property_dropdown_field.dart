import 'package:flutter/material.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';
import 'package:melos_core/config/language/locale_keys.g.dart';
import 'package:melos_core/config/res/config_imports.dart';
import 'package:melos_core/core/extensions/align_helper.dart';
import 'package:melos_core/core/extensions/sized_box_helper.dart';
import 'package:melos_core/core/helpers/text_style_manager.dart';
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
          style: AppTextStyles.semiBold.copyWith(
            color: AppColors.sokoonGray,
            fontSize: 12.sp,
          ),
          textAlign: TextAlign.start,
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
              value: items.contains(value) ? value : null,
              isExpanded: true,
              hint: AppText(
                LocaleKeys.ownerAddPropertyChoose,
                style: AppTextStyles.semiBold.copyWith(
                  color: AppColors.sokoonMuted,
                  fontSize: 13.sp,
                ),
              ).endWidget,
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
                    AppText(
                      item,
                      style: AppTextStyles.bold15.copyWith(
                        color: AppColors.sokoonTeal,
                        fontSize: 15.sp,
                        height: 1.45,
                      ),
                      maxLines: 1,
                      overflow: TextOverflow.ellipsis,
                    ).endWidget,
                ];
              },
              items: [
                for (final item in items)
                  DropdownMenuItem<String>(
                    value: item,
                    alignment: AlignmentDirectional.centerEnd,
                    child: AppText(
                      item,
                      style: AppTextStyles.bold13.copyWith(
                        color: AppColors.sokoonNavy,
                        fontSize: 13.sp,
                        height: 1.45,
                      ),
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
