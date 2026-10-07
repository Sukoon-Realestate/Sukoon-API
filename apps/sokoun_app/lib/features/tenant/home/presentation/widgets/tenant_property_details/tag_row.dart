import 'package:flutter/material.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';
import 'package:melos_core/config/language/locale_keys.g.dart';
import 'package:melos_core/config/res/config_imports.dart';
import 'package:melos_core/core/helpers/text_style_manager.dart';
import 'package:melos_core/core/widgets/app_text.dart';
import 'package:sokoun_app/features/tenant/home/data/models/tenant_property_content.dart';

class TenantPropertyTagRow extends StatelessWidget {
  const TenantPropertyTagRow({super.key, required this.property});

  final TenantPropertyDetailsContent property;

  @override
  Widget build(BuildContext context) {
    return Wrap(
      spacing: 7.w,
      runSpacing: 7.h,
      alignment: WrapAlignment.end,
      children: [
        if (property.selection?.scope case final scope?)
          _SmallTag(
            label: scope.label,
            backgroundColor: AppColors.tealAlpha09,
            textColor: context.appColor(AppColors.sokoonTeal),
          ),
        _SmallTag(
          label: property.hasRentalOffers
              ? '${LocaleKeys.rentalParentPropertyType}: ${property.propertyType}'
              : property.propertyType,
          backgroundColor: AppColors.tealAlpha09,
          textColor: context.appColor(AppColors.sokoonTeal),
        ),
        if (property.isFurnished && !property.hasRentalOffers)
          _SmallTag(
            label: LocaleKeys.tenantPropertyDetailsFurnished,
            backgroundColor: context.appColor(
              AppColors.grayBackground,
              surface: true,
            ),
            textColor: context.appColor(AppColors.sokoonGray),
          ),
        if (property.isVerified)
          _SmallTag(
            label: '${LocaleKeys.verified} ✓',
            backgroundColor: AppColors.greenAlpha09,
            textColor: context.appColor(AppColors.green),
          ),
      ],
    );
  }
}

class _SmallTag extends StatelessWidget {
  const _SmallTag({
    required this.label,
    required this.backgroundColor,
    required this.textColor,
  });

  final String label;
  final Color backgroundColor;
  final Color textColor;

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: EdgeInsets.symmetric(horizontal: 9.w, vertical: 4.h),
      decoration: BoxDecoration(
        color: context.appColor(backgroundColor, surface: true),
        borderRadius: BorderRadius.circular(8.r),
      ),
      child: AppText(
        label,
        style: AppTextStyles.extraBold.copyWith(
          color: context.appColor(textColor),
          fontSize: 11.sp,
        ),
      ),
    );
  }
}
