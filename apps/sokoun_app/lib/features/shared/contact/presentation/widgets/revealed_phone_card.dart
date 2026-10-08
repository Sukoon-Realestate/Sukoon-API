import 'package:flutter/material.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';
import 'package:melos_core/config/language/locale_keys.g.dart';
import 'package:melos_core/config/res/config_imports.dart';
import 'package:melos_core/core/helpers/text_style_manager.dart';
import 'package:melos_core/core/helpers/lancher_helper.dart';
import 'package:melos_core/core/widgets/app_text.dart';

class RevealedPhoneCard extends StatelessWidget {
  const RevealedPhoneCard({super.key, required this.phoneNumber});

  final String phoneNumber;

  @override
  Widget build(BuildContext context) => Container(
    padding: EdgeInsets.symmetric(horizontal: 13.w, vertical: 10.h),
    decoration: BoxDecoration(
      color: context.appColor(AppColors.greenPale, surface: true),
      borderRadius: BorderRadius.circular(14.r),
    ),
    child: Row(
      spacing: 10.w,
      children: [
        Expanded(
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              AppText(
                LocaleKeys.phoneNumber,
                style: AppTextStyles.regular12.copyWith(
                  color: context.appColor(AppColors.greenStrong),
                ),
              ),
              Directionality(
                textDirection: TextDirection.ltr,
                child: SelectableText(
                  phoneNumber,
                  style: AppTextStyles.bold15.copyWith(
                    color: context.appColor(AppColors.greenStrong),
                  ),
                ),
              ),
            ],
          ),
        ),
        IconButton(
          tooltip: LocaleKeys.contactCall,
          onPressed: () => LauncherHelper.callPhone(
            phone: phoneNumber.replaceAll(RegExp(r'[\s().-]'), ''),
          ),
          icon: Icon(
            Icons.phone_outlined,
            color: context.appColor(AppColors.greenStrong),
          ),
        ),
      ],
    ),
  );
}
