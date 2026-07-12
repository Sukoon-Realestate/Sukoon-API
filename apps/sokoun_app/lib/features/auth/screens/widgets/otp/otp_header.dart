import 'package:flutter/material.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';
import 'package:melos_core/config/language/locale_keys.g.dart';
import 'package:melos_core/config/res/config_imports.dart';
import 'package:melos_core/core/widgets/app_text.dart';

class OtpHeader extends StatelessWidget {
  const OtpHeader({super.key, this.onBack});

  final VoidCallback? onBack;

  @override
  Widget build(BuildContext context) {
    return SizedBox(
      height: 52.h,
      child: Stack(
        alignment: Alignment.center,
        children: [
          Align(
            alignment: AlignmentDirectional.centerStart,
            child: SizedBox.square(
              dimension: 36.r,
              child: DecoratedBox(
                decoration: BoxDecoration(
                  color: AppColors.grayBackground,
                  borderRadius: BorderRadius.circular(12.r),
                ),
                child: IconButton(
                  onPressed: onBack,
                  padding: EdgeInsets.zero,
                  icon: Icon(
                    Icons.arrow_back_ios_new_rounded,
                    color: AppColors.sokoonNavy,
                    size: 16.r,
                  ),
                ),
              ),
            ),
          ),
          AppText(
            LocaleKeys.verificationCode,
            color: AppColors.sokoonNavy,
            fontSize: 16.sp,
            fontWeight: FontWeight.w800,
            textAlign: TextAlign.center,
          ),
        ],
      ),
    );
  }
}
