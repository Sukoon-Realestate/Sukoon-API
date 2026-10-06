import 'package:flutter/material.dart';
import 'package:melos_core/config/language/locale_keys.g.dart';
import 'package:melos_core/core/navigation/navigator.dart';
import 'package:melos_core/core/widgets/app_text.dart';
import 'package:sokoun_app/features/owner/properties/data/models/owner_property_content.dart';
import 'package:sokoun_app/features/owner/advanced_analytics/presentation/screens/advanced_analytics_screen.dart';
import 'package:sokoun_app/features/owner/ai_assistant/data/models/listing_ai_facts.dart';
import 'package:sokoun_app/features/owner/ai_assistant/presentation/screens/listing_ai_screen.dart';
import '../screens/promotions_screen.dart';

class OwnerPropertyPremiumActions extends StatelessWidget {
  const OwnerPropertyPremiumActions({super.key, required this.property});
  final OwnerPropertyContent property;
  @override
  Widget build(BuildContext context) => Wrap(
    spacing: 8,
    runSpacing: 8,
    children: [
      TextButton.icon(
        onPressed: () {
          Go.back();
          Go.to(PromotionsScreen(property: property));
        },
        icon: const Icon(Icons.campaign_outlined),
        label: AppText(LocaleKeys.paidListingBoost),
      ),
      TextButton.icon(
        onPressed: () {
          Go.back();
          Go.to(AdvancedAnalyticsScreen(property: property));
        },
        icon: const Icon(Icons.insights_outlined),
        label: AppText(LocaleKeys.paidAdvancedAnalytics),
      ),
      TextButton.icon(
        onPressed: () {
          Go.back();
          Go.to(
            ListingAiScreen(
              propertyId: property.id,
              facts: ListingAiFacts.fromProperty(property),
            ),
          );
        },
        icon: const Icon(Icons.auto_awesome_outlined),
        label: AppText(LocaleKeys.paidAiAssistant),
      ),
    ],
  );
}
