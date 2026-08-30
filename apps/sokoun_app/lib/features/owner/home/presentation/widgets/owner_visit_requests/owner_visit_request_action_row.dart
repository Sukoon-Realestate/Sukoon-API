import 'package:flutter/material.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';
import 'package:melos_core/config/res/config_imports.dart';
import 'package:melos_core/core/extensions/sized_box_helper.dart';
import 'package:melos_core/core/widgets/app_text.dart';
import 'package:melos_core/config/language/locale_keys.g.dart';

class OwnerVisitRequestActionRow extends StatelessWidget {
  const OwnerVisitRequestActionRow({
    super.key,
    required this.onAcceptPressed,
    required this.onRejectPressed,
  });

  final VoidCallback onAcceptPressed;
  final VoidCallback onRejectPressed;

  @override
  Widget build(BuildContext context) {
    return Row(
      textDirection: TextDirection.rtl,
      children: [
        Expanded(
          child: _ActionButton(
            key: const ValueKey('owner-request-card-accept'),
            label: LocaleKeys.ownerVisitAccept,
            backgroundColor: AppColors.sokoonTeal,
            foregroundColor: AppColors.white,
            onPressed: onAcceptPressed,
          ),
        ),
        8.szW,
        Expanded(
          child: _ActionButton(
            key: const ValueKey('owner-request-card-reject'),
            label: LocaleKeys.ownerVisitReject,
            backgroundColor: AppColors.white,
            foregroundColor: AppColors.sokoonRose,
            borderColor: AppColors.sokoonRose,
            onPressed: onRejectPressed,
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
    required this.onPressed,
    this.borderColor,
    super.key,
  });

  final String label;
  final Color backgroundColor;
  final Color foregroundColor;
  final VoidCallback onPressed;
  final Color? borderColor;

  @override
  Widget build(BuildContext context) {
    return Material(
      color: AppColors.transparent,
      child: InkWell(
        onTap: onPressed,
        borderRadius: BorderRadius.circular(10.r),
        child: Container(
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
        ),
      ),
    );
  }
}
