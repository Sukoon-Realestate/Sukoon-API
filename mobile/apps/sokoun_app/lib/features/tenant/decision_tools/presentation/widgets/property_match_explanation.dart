import 'package:flutter/material.dart';
import 'package:melos_core/config/language/locale_keys.g.dart';
import 'package:melos_core/core/widgets/app_text.dart';
import 'package:sokoun_app/features/tenant/home/data/models/property_details_model.dart';
import 'package:sokoun_app/features/tenant/home/data/models/property_search_model.dart';
import '../../data/property_match_data.dart';

class PropertyMatchExplanation extends StatelessWidget {
  const PropertyMatchExplanation({
    super.key,
    required this.property,
    required this.preferences,
  });
  final PropertyDetailsModel property;
  final PropertySearchFilters preferences;
  @override
  Widget build(BuildContext context) {
    final reasons = PropertyMatchData.reasons(property, preferences);
    if (reasons.isEmpty) return const SizedBox.shrink();
    final labels = {
      PropertyMatchReason.price: LocaleKeys.freeMatchPrice,
      PropertyMatchReason.period: LocaleKeys.freeMatchPeriod,
      PropertyMatchReason.type: LocaleKeys.freeMatchType,
      PropertyMatchReason.amenities: LocaleKeys.freeMatchAmenities,
      PropertyMatchReason.bedrooms: LocaleKeys.freeMatchBedrooms,
      PropertyMatchReason.verified: LocaleKeys.freeMatchVerified,
    };
    return Padding(
      padding: const EdgeInsets.only(bottom: 16),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          AppText(LocaleKeys.freeWhyMatches, fontWeight: FontWeight.bold),
          const SizedBox(height: 8),
          for (final reason in reasons)
            AppText('• ${labels[reason]}', height: 1.6),
        ],
      ),
    );
  }
}
