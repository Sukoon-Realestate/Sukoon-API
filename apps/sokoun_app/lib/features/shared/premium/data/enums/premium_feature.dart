import 'package:melos_core/config/language/locale_keys.g.dart';

enum PremiumFeature {
  listingBoost('listing_boost'),
  priorityAlerts('priority_alerts'),
  advancedAnalytics('advanced_analytics'),
  aiAssistant('ai_assistant'),
  digitalLeases('digital_leases'),
  rentManagement('rent_management');

  const PremiumFeature(this.apiValue);
  final String apiValue;
  static PremiumFeature? fromValue(Object? value) => PremiumFeature.values
      .where((feature) => feature.apiValue == value)
      .firstOrNull;
  String get label => switch (this) {
    listingBoost => LocaleKeys.paidListingBoost,
    priorityAlerts => LocaleKeys.paidPriorityAlerts,
    advancedAnalytics => LocaleKeys.paidAdvancedAnalytics,
    aiAssistant => LocaleKeys.paidAiAssistant,
    digitalLeases => LocaleKeys.paidDigitalLeases,
    rentManagement => LocaleKeys.paidRentManagement,
  };
  bool get ownerOnly =>
      this == listingBoost || this == advancedAnalytics || this == aiAssistant;
  bool get tenantOnly => this == priorityAlerts;
}
