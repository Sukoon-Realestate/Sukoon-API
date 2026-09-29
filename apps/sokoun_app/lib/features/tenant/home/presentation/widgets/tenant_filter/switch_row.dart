import 'package:flutter/material.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';
import 'package:melos_core/config/res/config_imports.dart';
import 'package:melos_core/core/extensions/sized_box_helper.dart';
import 'package:melos_core/core/widgets/app_text.dart';

class SwitchRow extends StatelessWidget {
  const SwitchRow({
    super.key,
    required this.title,
    required this.subtitle,
    required this.value,
    required this.onChanged,
  });

  final String title;
  final String subtitle;
  final bool value;
  final ValueChanged<bool> onChanged;

  @override
  Widget build(BuildContext context) {
    return Row(
      children: [
        Expanded(
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              AppText(
                title,
                color: AppColors.sokoonNavy,
                fontSize: 13.sp,
                fontWeight: FontWeight.w700,
              ),
              3.szH,
              AppText(
                subtitle,
                color: AppColors.sokoonGray,
                fontSize: 11.sp,
                fontWeight: FontWeight.w500,
              ),
            ],
          ),
        ),
        Switch.adaptive(
          value: value,
          activeThumbColor: AppColors.sokoonTeal,
          activeTrackColor: AppColors.tealAlpha27,
          onChanged: onChanged,
        ),
      ],
    );
  }
}
