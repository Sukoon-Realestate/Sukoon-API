import 'package:flutter/material.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';
import 'package:melos_core/config/res/config_imports.dart';
import 'package:melos_core/core/helpers/text_style_manager.dart';
import 'package:melos_core/core/widgets/app_text.dart';
import 'package:melos_core/core/widgets/custom_loading.dart';
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
      spacing: 8.w,
      children: [
        Expanded(
          child: _ActionButton(
            label: LocaleKeys.ownerVisitAccept,
            backgroundColor: context.appColor(
              AppColors.sokoonTeal,
              surface: true,
            ),
            foregroundColor: AppColors.white,
            onPressed: onAcceptPressed,
            isLoading: isAccepting,
          ),
        ),
        Expanded(
          child: _ActionButton(
            label: LocaleKeys.ownerVisitReject,
            backgroundColor: context.appColor(AppColors.white, surface: true),
            foregroundColor: context.appColor(AppColors.sokoonRose),
            borderColor: context.appColor(AppColors.sokoonRose),
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
            color: context.appColor(backgroundColor, surface: true),
            borderRadius: BorderRadius.circular(10.r),
            border: Border.all(
              color: context.appColor(borderColor ?? backgroundColor),
            ),
          ),
          child: isLoading
              ? SizedBox.square(
                  dimension: 18.r,
                  child: CustomLoading.showLoadingView(
                    color: context.appColor(foregroundColor),
                    size: 18.r,
                  ),
                )
              : AppText(
                  label,
                  style: AppTextStyles.bold14.copyWith(
                    color: context.appColor(foregroundColor),
                    fontSize: 14.sp,
                    height: 1.45,
                  ),
                  textAlign: TextAlign.center,
                ),
        ),
      ),
    );
  }
}
