import 'package:flutter/material.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';
import 'package:melos_core/config/res/config_imports.dart';
import 'package:melos_core/core/widgets/app_text.dart';
import 'package:sokoun_app/shared_widgets/back_button.dart';

class ForgotPasswordAppBar extends StatelessWidget {
  const ForgotPasswordAppBar({
    super.key,
    required this.title,
    required this.onBack,
  });

  final String title;
  final VoidCallback onBack;

  @override
  Widget build(BuildContext context) {
    return Container(
      height: 52.h,
      padding: EdgeInsets.symmetric(horizontal: 24.w),
      decoration: const BoxDecoration(
        color: AppColors.white,
        border: Border(bottom: BorderSide(color: AppColors.grayPale)),
      ),
      child: Stack(
        alignment: Alignment.center,
        children: [
          Align(
            alignment: AlignmentDirectional.centerStart,
            child: SokoonBackButton(onTap: onBack),
          ),
          AppText(
            title,
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
