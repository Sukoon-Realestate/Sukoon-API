import 'package:flutter/material.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';
import 'package:melos_core/config/language/locale_keys.g.dart';
import 'package:melos_core/config/res/config_imports.dart';
import 'package:melos_core/core/extensions/sized_box_helper.dart';
import 'package:melos_core/core/widgets/app_text.dart';
import 'package:sokoun_app/features/tenant/home/data/models/tenant_property_content.dart';

class TenantPropertyPriceAndRating extends StatelessWidget {
  const TenantPropertyPriceAndRating({super.key, required this.property});

  final TenantPropertyDetailsContent property;

  @override
  Widget build(BuildContext context) {
    return Row(
      children: [
        Expanded(
          child: Align(
            alignment: AlignmentDirectional.centerStart,
            child: FittedBox(
              fit: BoxFit.scaleDown,
              child: Row(
                children: [
                  AppText(
                    LocaleKeys.tenantPropertyDetailsMonthlyPriceUnit,
                    color: AppColors.sokoonGray,
                    fontSize: 13.sp,
                    fontWeight: FontWeight.w500,
                  ),
                  6.szW,
                  AppText(
                    property.price,
                    color: AppColors.sokoonTeal,
                    fontSize: 24.sp,
                    fontWeight: FontWeight.w900,
                  ),
                ],
              ),
            ),
          ),
        ),
        8.szW,
        Row(
          children: [
            AppText('⭐', fontSize: 14.sp),
            4.szW,
            AppText(
              property.rating,
              color: AppColors.sokoonNavy,
              fontSize: 13.sp,
              fontWeight: FontWeight.w900,
            ),
            3.szW,
            AppText(
              '(${property.reviewCount})',
              color: AppColors.sokoonGray,
              fontSize: 12.sp,
              fontWeight: FontWeight.w500,
            ),
          ],
        ),
      ],
    );
  }
}
