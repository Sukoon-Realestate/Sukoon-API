import 'package:melos_core/config/language/locale_keys.g.dart';

enum PropertyPricePeriod {
  daily('daily'),
  weekly('weekly'),
  monthly('monthly'),
  yearly('yearly');

  const PropertyPricePeriod(this.value);
  final String value;

  String get label => switch (this) {
    PropertyPricePeriod.daily => LocaleKeys.ownerAddPropertyDay,
    PropertyPricePeriod.weekly => LocaleKeys.ownerAddPropertyWeek,
    PropertyPricePeriod.monthly => LocaleKeys.ownerAddPropertyMonth,
    PropertyPricePeriod.yearly => LocaleKeys.ownerAddPropertyYear,
  };

  static PropertyPricePeriod? fromValue(String value) =>
      values.where((period) => period.value == value).firstOrNull;
}
