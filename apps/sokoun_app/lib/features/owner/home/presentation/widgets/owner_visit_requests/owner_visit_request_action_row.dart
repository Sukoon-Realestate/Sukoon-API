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
    this.isAccepting = false,
    this.isRejecting = false,
  });

  final VoidCallback? onAcceptPressed;
  final VoidCallback? onRejectPressed;
  final bool isAccepting;
  final bool isRejecting;

  @override
  Widget build(BuildContext context) {
    return Row(
      children: [
        Expanded(
          child: _ActionButton(
            label: LocaleKeys.ownerVisitAccept,
            backgroundColor: AppColors.sokoonTeal,
            foregroundColor: AppColors.white,
            onPressed: onAcceptPressed,
            isLoading: isAccepting,
          ),
        ),
        8.szW,
        Expanded(
          child: _ActionButton(
            label: LocaleKeys.ownerVisitReject,
            backgroundColor: AppColors.white,
            foregroundColor: AppColors.sokoonRose,
            borderColor: AppColors.sokoonRose,
            onPressed: onRejectPressed,
            isLoading: isRejecting,
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
    this.isLoading = false,
    this.borderColor,
  });

  final String label;
  final Color backgroundColor;
  final Color foregroundColor;
  final VoidCallback? onPressed;
  final Color? borderColor;
  final bool isLoading;

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
          child: isLoading
              ? SizedBox.square(
                  dimension: 18.r,
                  child: CircularProgressIndicator(
                    strokeWidth: 2,
                    color: foregroundColor,
                  ),
                )
              : AppText(
                  label,
                  color: foregroundColor,
                  fontSize: 14.sp,
                  fontWeight: FontWeight.w700,
                  textAlign: TextAlign.center,
                ),
        ),
      ),
    );
  }
}
