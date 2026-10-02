import 'package:flutter/material.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';
import 'package:melos_core/config/res/config_imports.dart';
import 'package:melos_core/core/helpers/text_style_manager.dart';
import 'package:melos_core/core/widgets/app_text.dart';
import 'package:sokoun_app/features/tenant/home/data/models/tenant_property_content.dart';
import 'package:sokoun_app/features/shared/reviews/presentation/widgets/property_rating_summary.dart';

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
                    property.pricePeriodLabel,
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
        if (property.id.isNotEmpty)
          PropertyRatingSummary(
            key: ValueKey(property.id),
            propertyId: property.id,
          ),
      ],
    );
  }
}
