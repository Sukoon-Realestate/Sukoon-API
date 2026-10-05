import 'package:flutter/material.dart';
import 'package:easy_localization/easy_localization.dart';
import 'package:melos_core/config/language/locale_keys.g.dart';
import 'package:melos_core/config/res/config_imports.dart';
import 'package:melos_core/core/helpers/text_style_manager.dart';
import 'package:melos_core/core/widgets/app_text.dart';
import 'package:sokoun_app/features/tenant/home/data/models/tenant_property_content.dart';

import 'info_section.dart';

class TenantPropertyListingInformation extends StatelessWidget {
  const TenantPropertyListingInformation({super.key, required this.property});

  final TenantPropertyDetailsContent property;

  String _formatDate(String value, String locale) {
    final DateTime? date = DateTime.tryParse(value);
    return date == null
        ? value
        : DateFormat.yMMMd(locale).format(date.toLocal());
  }

  String get _statusLabel => switch (property.status) {
    'under_review' || 'pending' => LocaleKeys.ownerPropertyStatusPending,
    'verified' || 'approved' => LocaleKeys.ownerPropertyStatusVerified,
    'hidden' => LocaleKeys.ownerPropertyStatusHidden,
    'rejected' => LocaleKeys.ownerPropertyStatusRejected,
    'rented' => LocaleKeys.ownerPropertyStatusRented,
    _ => property.status,
  };

  @override
  Widget build(BuildContext context) {
    final List<({String label, String value})> facts = [
      (label: LocaleKeys.ownerAddPropertyCountry, value: property.country),
      (
        label: LocaleKeys.ownerAddPropertyGovernorate,
        value: property.governorateName,
      ),
      (label: LocaleKeys.ownerAddPropertyCity, value: property.cityName),
      (
        label: LocaleKeys.ownerAddPropertyNeighborhood,
        value: property.district,
      ),
      (label: LocaleKeys.ownerAddPropertyStreet, value: property.street),
      (label: LocaleKeys.ownerAddPropertySpace, value: property.space),
      (
        label: LocaleKeys.tenantPropertyDetailsListingStatus,
        value: _statusLabel,
      ),
      (
        label: LocaleKeys.tenantPropertyDetailsListedAt,
        value: _formatDate(property.createdAt, context.locale.toString()),
      ),
      (
        label: LocaleKeys.tenantPropertyDetailsUpdatedAt,
        value: _formatDate(property.updatedAt, context.locale.toString()),
      ),
    ];
    return TenantPropertyInfoSection(
      title: LocaleKeys.tenantPropertyDetailsListingInformation,
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        spacing: 12,
        children: [
          for (final fact in facts)
            if (fact.value.trim().isNotEmpty)
              Column(
                crossAxisAlignment: CrossAxisAlignment.stretch,
                spacing: 4,
                children: [
                  AppText(
                    fact.label,
                    style: AppTextStyles.regular12.copyWith(
                      color: AppColors.sokoonGray,
                    ),
                  ),
                  AppText(
                    fact.value,
                    style: AppTextStyles.medium13.copyWith(
                      color: AppColors.sokoonNavy,
                    ),
                  ),
                ],
              ),
        ],
      ),
    );
  }
}
