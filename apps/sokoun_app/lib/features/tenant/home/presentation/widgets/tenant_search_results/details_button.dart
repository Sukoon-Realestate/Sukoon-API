import 'package:flutter/material.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';
import 'package:melos_core/config/language/locale_keys.g.dart';
import 'package:melos_core/config/res/config_imports.dart';
import 'package:melos_core/core/helpers/text_style_manager.dart';
import 'package:melos_core/core/navigation/navigator.dart';
import 'package:melos_core/core/widgets/app_text.dart';
import 'package:sokoun_app/features/tenant/home/presentation/screens/property_details_screen.dart';

class DetailsButton extends StatelessWidget {
  const DetailsButton({super.key, required this.propertyId});

  final String propertyId;

  void _openDetails() {
    if (propertyId.isEmpty) return;
    Go.to(PropertyDetailsScreen(propertyId: propertyId));
  }

  @override
  Widget build(BuildContext context) {
    return GestureDetector(
      onTap: _openDetails,
      behavior: HitTestBehavior.opaque,
      child: Container(
        height: 34.h,
        padding: EdgeInsets.symmetric(horizontal: 16.w),
        alignment: Alignment.center,
        decoration: BoxDecoration(
          color: AppColors.sokoonTeal,
          borderRadius: BorderRadius.circular(10.r),
        ),
        child: AppText(
          LocaleKeys.landingDetails,
          style: AppTextStyles.extraBold13.copyWith(
            color: AppColors.white,
            fontSize: 13.sp,
            height: 1.45,
          ),
        ),
      ),
    );
  }
}
