import 'package:flutter/material.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';
import 'package:melos_core/config/language/locale_keys.g.dart';
import 'package:melos_core/core/extensions/string_extension.dart';
import 'package:melos_core/core/navigation/navigator.dart';
import 'package:sokoun_app/features/tenant/home/data/models/home_page_model.dart';
import 'package:sokoun_app/features/tenant/home/presentation/screens/property_details_screen.dart';

import 'tenant_suggested_properties_empty_state.dart';
import 'tenant_property_card.dart';

class SuggestedPropertiesSection extends StatelessWidget {
  const SuggestedPropertiesSection({required this.properties, super.key});

  final List<HomePropertyModel> properties;

  @override
  Widget build(BuildContext context) {
    if (properties.isEmpty) {
      return const TenantSuggestedPropertiesEmptyState();
    }

    return Column(
      spacing: 12.h,
      children: properties
          .map(
            (property) => GestureDetector(
              onTap: () =>
                  Go.to(PropertyDetailsScreen(propertyId: property.id)),
              behavior: HitTestBehavior.opaque,
              child: TenantPropertyCard(
                title: property.title,
                rating: property.rate.toStringAsFixed(1),
                area:
                    '${property.area} ${LocaleKeys.tenantSearchResultsSquareMeters}',
                price: _formattedPrice(property),
                icon: _propertyIcon(property.propertyType),
                imageUrl: property.mainImage,
              ),
            ),
          )
          .toList(growable: false),
    );
  }

  String _formattedPrice(HomePropertyModel property) {
    final double price =
        double.tryParse(property.price.replaceAll(',', '')) ?? 0;
    return '${price.toCurrency()} ${LocaleKeys.favoritesCurrencyShort}/${_pricePeriodLabel(property.pricePeriod)}';
  }

  String _pricePeriodLabel(String pricePeriod) {
    return switch (pricePeriod) {
      'daily' => LocaleKeys.tenantFilterDaily,
      'weekly' => LocaleKeys.tenantFilterWeekly,
      'yearly' => LocaleKeys.tenantFilterYearly,
      _ => LocaleKeys.tenantFilterMonthly,
    };
  }

  IconData _propertyIcon(String propertyType) {
    return switch (propertyType) {
      'studio' => Icons.meeting_room_outlined,
      'apartment' => Icons.apartment_rounded,
      _ => Icons.home_outlined,
    };
  }
}
