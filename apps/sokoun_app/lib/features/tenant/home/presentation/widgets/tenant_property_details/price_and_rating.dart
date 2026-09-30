import 'package:flutter/material.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';
import 'package:melos_core/config/language/locale_keys.g.dart';
import 'package:melos_core/config/res/config_imports.dart';
import 'package:melos_core/core/extensions/sized_box_helper.dart';
import 'package:melos_core/core/helpers/text_style_manager.dart';
import 'package:melos_core/core/widgets/app_text.dart';
import 'package:sokoun_app/features/tenant/home/data/models/tenant_property_content.dart';

class TenantPropertyPriceAndRating extends StatelessWidget {
  const TenantPropertyPriceAndRating({super.key, required this.property});

  final TenantPropertyDetailsContent property;

  @override
  Widget build(BuildContext context) {
    return Row(
      spacing: 8.w,
      children: [
        Expanded(
          child: Align(
            alignment: AlignmentDirectional.centerStart,
            child: FittedBox(
              fit: BoxFit.scaleDown,
              child: Row(
                spacing: 6.w,
                children: [
                  AppText(
                    LocaleKeys.tenantPropertyDetailsMonthlyPriceUnit,
                    style: AppTextStyles.medium13.copyWith(
                      color: AppColors.sokoonGray,
                      fontSize: 13.sp,
                      height: 1.45,
                    ),
                  ),
                  AppText(
                    property.price,
                    style: AppTextStyles.extraBold.copyWith(
                      color: AppColors.sokoonTeal,
                      fontSize: 24.sp,
                    ),
                  ),
                ],
              ),
            ),
          ),
        ),
        Row(
          children: [
            AppText(
              '⭐',
              style: AppTextStyles.regular14.copyWith(
                fontSize: 14.sp,
                height: 1.45,
              ),
            ),
            4.szW,
            AppText(
              property.rating,
              style: AppTextStyles.extraBold13.copyWith(
                color: AppColors.sokoonNavy,
                fontSize: 13.sp,
                height: 1.45,
              ),
            ),
            3.szW,
            AppText(
              '(${property.reviewCount})',
              style: AppTextStyles.medium12.copyWith(
                color: AppColors.sokoonGray,
                fontSize: 12.sp,
                height: 1.45,
              ),
            ),
          ],
        ),
      ],
    );
  }
}
