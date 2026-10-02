import 'package:melos_core/config/language/locale_keys.g.dart';

enum ProfileSetting {
  visitNotifications('visit_notifications'),
  promotions('promotions_and_updates'),
  shareLocation('share_location_for_search'),
  showProfile('show_profile_in_search');

  const ProfileSetting(this.apiKey);
  final String apiKey;
  String get label => switch (this) {
    visitNotifications => LocaleKeys.profileVisitNotifications,
    promotions => LocaleKeys.profilePromotions,
    shareLocation => LocaleKeys.profileShareLocation,
    showProfile => LocaleKeys.profileShowInSearch,
  };
}
