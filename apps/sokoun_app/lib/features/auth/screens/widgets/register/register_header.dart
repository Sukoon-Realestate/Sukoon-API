import 'package:flutter/material.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';
import 'package:melos_core/config/language/locale_keys.g.dart';
import 'package:melos_core/config/res/config_imports.dart';
import 'package:melos_core/core/extensions/sized_box_helper.dart';
import 'package:melos_core/core/widgets/app_text.dart';

class RegisterHeader extends StatelessWidget {
  const RegisterHeader({super.key, this.onBack});

  final VoidCallback? onBack;

  @override
  Widget build(BuildContext context) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.stretch,
      children: [
        Align(
          alignment: AlignmentDirectional.centerEnd,
          child: SizedBox.square(
            dimension: 36.r,
            child: DecoratedBox(
              decoration: BoxDecoration(
                color: AppColors.white,
                borderRadius: BorderRadius.circular(12.r),
                border: Border.all(color: AppColors.sokoonBorder),
              ),
              child: IconButton(
                onPressed: onBack,
                padding: EdgeInsets.zero,
                icon: Icon(
                  Icons.arrow_forward_ios_rounded,
                  color: AppColors.sokoonNavy,
                  size: 16.r,
                ),
              ),
            ),
          ),
        ),
        14.szH,
        AppText(
          LocaleKeys.createAccount,
          color: AppColors.sokoonNavy,
          fontSize: 24.sp,
          fontWeight: FontWeight.w900,
        ),
        6.szH,
        AppText(
          LocaleKeys.registerJourneySubtitle,
          color: AppColors.sokoonGray,
          fontSize: 14.sp,
          fontWeight: FontWeight.w500,
        ),
      ],
    );
  }
}
