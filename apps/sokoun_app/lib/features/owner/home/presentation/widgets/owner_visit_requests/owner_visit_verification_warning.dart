import 'package:flutter/material.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';
import 'package:melos_core/config/res/config_imports.dart';
import 'package:melos_core/core/helpers/text_style_manager.dart';
import 'package:melos_core/core/widgets/app_text.dart';

class OwnerVisitVerificationWarning extends StatelessWidget {
  const OwnerVisitVerificationWarning({super.key, required this.message});

  final String message;

  @override
  Widget build(BuildContext context) => Container(
    padding: EdgeInsets.all(12.r),
    decoration: BoxDecoration(
      color: AppColors.amberPale,
      borderRadius: BorderRadius.circular(12.r),
    ),
    child: Row(
      spacing: 8.w,
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Icon(Icons.shield_outlined, color: AppColors.amber, size: 20.r),
        Expanded(
          child: AppText(
            message,
            style: AppTextStyles.regular12.copyWith(
              color: AppColors.sokoonNavy,
            ),
          ),
        ),
      ],
    ),
  );
}
