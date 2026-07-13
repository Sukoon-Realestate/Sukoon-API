import 'package:flutter/material.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';
import 'package:melos_core/config/res/config_imports.dart';
import 'package:melos_core/core/extensions/sized_box_helper.dart';
import 'package:melos_core/core/widgets/app_text.dart';

class OwnerVisitRequestActionRow extends StatelessWidget {
  const OwnerVisitRequestActionRow({super.key});

  @override
  Widget build(BuildContext context) {
    return Row(
      textDirection: TextDirection.ltr,
      children: [
        Expanded(
          child: _ActionButton(
            label: 'قبول',
            backgroundColor: AppColors.sokoonTeal,
            foregroundColor: AppColors.white,
          ),
        ),
        8.szW,
        Expanded(
          child: _ActionButton(
            label: 'رفض',
            backgroundColor: AppColors.white,
            foregroundColor: AppColors.sokoonRose,
            borderColor: AppColors.sokoonRose,
          ),
        ),
      ],
    );
  }
}

class _ActionButton extends StatelessWidget {
  const _ActionButton({
    required this.label,
    required this.backgroundColor,
    required this.foregroundColor,
    this.borderColor,
  });

  final String label;
  final Color backgroundColor;
  final Color foregroundColor;
  final Color? borderColor;

  @override
  Widget build(BuildContext context) {
    return Container(
      height: 40.h,
      alignment: Alignment.center,
      decoration: BoxDecoration(
        color: backgroundColor,
        borderRadius: BorderRadius.circular(10.r),
        border: Border.all(color: borderColor ?? backgroundColor),
      ),
      child: AppText(
        label,
        color: foregroundColor,
        fontSize: 14.sp,
        fontWeight: FontWeight.w900,
        textAlign: TextAlign.center,
      ),
    );
  }
}
