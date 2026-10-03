import 'package:flutter/material.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';
import 'package:melos_core/config/language/locale_keys.g.dart';
import 'package:melos_core/config/res/config_imports.dart';
import 'package:sokoun_app/features/shared/finance/presentation/egyptian_pound_text.dart';
import 'package:melos_core/core/helpers/text_style_manager.dart';
import 'package:melos_core/core/widgets/app_text.dart';
import 'package:sokoun_app/features/tenant/home/data/models/tenant_property_content.dart';

import 'info_section.dart';

class TenantPropertyRentalDetails extends StatelessWidget {
  const TenantPropertyRentalDetails({super.key, required this.property});

  final TenantPropertyDetailsContent property;

  String get _suitableFor => switch (property.suitableFor) {
    'all' => LocaleKeys.ownerAddPropertyEveryone,
    'males_only' => LocaleKeys.ownerAddPropertyMalesOnly,
    'females_only' => LocaleKeys.ownerAddPropertyFemalesOnly,
    'families' => LocaleKeys.ownerAddPropertyFamilies,
    'individuals' || 'singles' => LocaleKeys.ownerAddPropertyIndividuals,
    'shared' => LocaleKeys.ownerAddPropertyShared,
    _ => property.suitableFor,
  };

  @override
  Widget build(BuildContext context) {
    final rows = <({IconData icon, String label, String value})>[
      if (property.floor != null)
        (
          icon: Icons.layers_outlined,
          label: LocaleKeys.ownerAddPropertyFloor,
          value: '${property.floor}',
        ),
      if (property.suitableFor.trim().isNotEmpty)
        (
          icon: Icons.people_outline_rounded,
          label: LocaleKeys.ownerAddPropertySuitableFor,
          value: _suitableFor,
        ),
      if (property.smokingAllowed != null)
        (
          icon: property.smokingAllowed == true
              ? Icons.smoking_rooms_outlined
              : Icons.smoke_free_outlined,
          label: LocaleKeys.tenantPropertyDetailsSmokingPolicy,
          value: property.smokingAllowed == true
              ? LocaleKeys.tenantPropertyDetailsSmokingAllowed
              : LocaleKeys.tenantPropertyDetailsSmokingNotAllowed,
        ),
      if (property.buildingYear > 0)
        (
          icon: Icons.calendar_today_outlined,
          label: LocaleKeys.tenantPropertyDetailsBuildingYear,
          value: '${property.buildingYear}',
        ),
      if (property.deposit.trim().isNotEmpty)
        (
          icon: Icons.account_balance_wallet_outlined,
          label: LocaleKeys.tenantPropertyDetailsDeposit,
          value: EgyptianPoundText.format(property.deposit),
        ),
    ];
    if (rows.isEmpty) return const SizedBox.shrink();

    return TenantPropertyInfoSection(
      title: LocaleKeys.tenantPropertyDetailsRentalDetails,
      child: Column(
        children: [
          for (final (index, row) in rows.indexed)
            Container(
              padding: EdgeInsets.symmetric(vertical: 12.h),
              decoration: BoxDecoration(
                border: index < rows.length - 1
                    ? const Border(
                        bottom: BorderSide(color: AppColors.sokoonBorder),
                      )
                    : null,
              ),
              child: Row(
                spacing: 10.w,
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Icon(row.icon, color: AppColors.sokoonTeal, size: 20.r),
                  Expanded(
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      spacing: 4.h,
                      children: [
                        AppText(
                          row.label,
                          style: AppTextStyles.regular12.copyWith(
                            color: AppColors.sokoonGray,
                          ),
                        ),
                        AppText(
                          row.value,
                          style: AppTextStyles.medium13.copyWith(
                            color: AppColors.sokoonNavy,
                            fontSize: 14.sp,
                          ),
                        ),
                      ],
                    ),
                  ),
                ],
              ),
            ),
        ],
      ),
    );
  }
}
