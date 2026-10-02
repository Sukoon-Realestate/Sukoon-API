import 'package:flutter/material.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';
import 'package:melos_core/config/res/config_imports.dart';
import 'package:melos_core/core/helpers/text_style_manager.dart';
import 'package:melos_core/core/widgets/app_text.dart';
import 'package:sokoun_app/features/owner/visits/imports.dart';

class OwnerVisitRequestStatusBanner extends StatelessWidget {
  const OwnerVisitRequestStatusBanner({
    super.key,
    required this.status,
    this.label = '',
  });

  final OwnerVisitRequestStatus status;
  final String label;

  Color get _backgroundColor {
    if (status.isAccepted || status.isCompleted) {
      return AppColors.greenPale;
    }
    if (status.isRejected) {
      return AppColors.redPale;
    }
    return status.canDecide ? AppColors.amberPale : AppColors.grayBackground;
  }

  Color get _foregroundColor {
    if (status.isAccepted || status.isCompleted) {
      return AppColors.green;
    }
    if (status.isRejected) {
      return AppColors.red;
    }
    return status.canDecide ? AppColors.amber : AppColors.sokoonGray;
  }

  @override
  Widget build(BuildContext context) {
    return Container(
      width: double.infinity,
      padding: EdgeInsets.symmetric(horizontal: 12.w, vertical: 10.h),
      alignment: Alignment.center,
      decoration: BoxDecoration(
        color: _backgroundColor,
        borderRadius: BorderRadius.circular(10.r),
        border: Border.all(color: _foregroundColor.withValues(alpha: 0.2)),
      ),
      child: AppText(
        label.trim().isNotEmpty ? label : status.label,
        style: AppTextStyles.bold13.copyWith(
          color: _foregroundColor,
          fontSize: 13.sp,
          height: 1.45,
        ),
        textAlign: TextAlign.center,
      ),
    );
  }
}
