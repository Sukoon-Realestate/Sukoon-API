import 'package:flutter/material.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';
import 'package:melos_core/config/language/locale_keys.g.dart';
import 'package:melos_core/config/res/config_imports.dart';
import 'package:melos_core/core/helpers/text_style_manager.dart';
import 'package:melos_core/core/widgets/app_text.dart';

class TenantPropertyOwnershipVerifiedBanner extends StatelessWidget {
  const TenantPropertyOwnershipVerifiedBanner({super.key});

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: EdgeInsets.all(14.w),
      decoration: BoxDecoration(
        color: AppColors.greenAlpha06,
        borderRadius: BorderRadius.circular(14.r),
        border: Border.all(color: AppColors.greenAlpha19),
      ),
      child: Row(
        spacing: 8.w,
        children: [
          Icon(
            Icons.verified_user_outlined,
            color: context.appColor(AppColors.greenStrong),
            size: 18.r,
          ),
          Expanded(
            child: AppText(
              LocaleKeys.tenantPropertyDetailsOwnershipVerified,
              style: AppTextStyles.bold13.copyWith(
                color: context.appColor(AppColors.greenStrong),
                fontSize: 13.sp,
                height: 1.45,
              ),
            ),
          ),
        ],
      ),
    );
  }
}
