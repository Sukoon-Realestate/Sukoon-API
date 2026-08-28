import 'package:flutter/material.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';
import 'package:melos_core/config/language/locale_keys.g.dart';
import 'package:melos_core/config/res/config_imports.dart';
import 'package:melos_core/core/extensions/sized_box_helper.dart';
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
        children: [
          Icon(
            Icons.verified_user_outlined,
            color: AppColors.green,
            size: 18.r,
          ),
          8.szW,
          Expanded(
            child: AppText(
              LocaleKeys.tenantPropertyDetailsOwnershipVerified,
              color: AppColors.green,
              fontSize: 13.sp,
              fontWeight: FontWeight.w900,
            ),
          ),
        ],
      ),
    );
  }
}
