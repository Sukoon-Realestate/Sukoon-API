import 'package:flutter/material.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';
import 'package:melos_core/config/language/locale_keys.g.dart';
import 'package:melos_core/config/res/config_imports.dart';
import 'package:melos_core/core/helpers/text_style_manager.dart';
import 'package:melos_core/core/navigation/navigator.dart';
import 'package:melos_core/core/widgets/app_text.dart';
import 'package:sokoun_app/features/tenant/home/presentation/screens/tenant_search_screen.dart';

class HomeSearchBox extends StatelessWidget {
  const HomeSearchBox({super.key});

  @override
  Widget build(BuildContext context) {
    return GestureDetector(
      onTap: () => Go.to(const TenantSearchScreen()),
      child: Container(
        height: 52.h,
        padding: EdgeInsetsDirectional.only(start: 16.w, end: 8.w),
        decoration: BoxDecoration(
          color: context.appColor(AppColors.white, surface: true),
          borderRadius: BorderRadius.circular(16.r),
          border: Border.all(color: context.appColor(AppColors.sokoonBorder)),
        ),
        child: Row(
          spacing: 12.w,
          children: [
            Icon(
              Icons.search_rounded,
              color: context.appColor(AppColors.sokoonMuted),
              size: 20.r,
            ),
            Expanded(
              child: AppText(
                LocaleKeys.tenantHomeSearchAreaHint,
                style: AppTextStyles.regular14.copyWith(
                  color: context.appColor(AppColors.sokoonMuted),
                  fontSize: 14.sp,
                  height: 1.45,
                ),
                overflow: TextOverflow.ellipsis,
              ),
            ),
            Container(
              width: 34.r,
              height: 34.r,
              decoration: BoxDecoration(
                color: context.appColor(AppColors.sokoonTeal, surface: true),
                borderRadius: BorderRadius.circular(12.r),
              ),
              child: Icon(
                Icons.tune_rounded,
                color: AppColors.white,
                size: 17.r,
              ),
            ),
          ],
        ),
      ),
    );
  }
}
