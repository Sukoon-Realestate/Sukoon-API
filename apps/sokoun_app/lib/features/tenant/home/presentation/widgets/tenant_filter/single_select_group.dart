import 'package:flutter/material.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';
import 'package:melos_core/config/res/config_imports.dart';
import 'package:melos_core/core/extensions/sized_box_helper.dart';
import 'package:melos_core/core/helpers/text_style_manager.dart';
import 'package:melos_core/core/widgets/app_text.dart';
import 'package:sokoun_app/features/tenant/home/data/models/property_filter_options_model.dart';

import 'filter_chip_wrap.dart';

class SingleSelectGroup extends StatelessWidget {
  const SingleSelectGroup({
    super.key,
    required this.title,
    required this.options,
    required this.selectedValue,
    required this.onSelected,
  });

  final String title;
  final List<TenantFilterOption> options;
  final String selectedValue;
  final ValueChanged<String> onSelected;

  @override
  Widget build(BuildContext context) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.stretch,
      children: [
        AppText(
          title,
          style: AppTextStyles.semiBold.copyWith(
            color: AppColors.sokoonGray,
            fontSize: 12.sp,
          ),
          textAlign: TextAlign.start,
        ),
        8.szH,
        FilterChipWrap(
          options: options,
          selectedValues: {selectedValue},
          onSelected: onSelected,
        ),
      ],
    );
  }
}
