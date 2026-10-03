import 'package:melos_core/config/language/locale_keys.g.dart';

import '../data/egyptian_pound.dart';

/// Localized money text, independent of currency labels returned by the API.
abstract final class EgyptianPoundText {
  static String get symbol => LocaleKeys.egyptianPoundShort;

  static String format(Object? amount, {String period = ''}) =>
      '${EgyptianPound.formatAmount(amount)} ${unit(period)}';

  static String unit(String period) => switch (period) {
    'daily' => LocaleKeys.tenantPropertyDetailsDailyPriceUnit,
    'weekly' => LocaleKeys.tenantPropertyDetailsWeeklyPriceUnit,
    'monthly' => LocaleKeys.tenantPropertyDetailsMonthlyPriceUnit,
    'yearly' => LocaleKeys.tenantPropertyDetailsYearlyPriceUnit,
    _ => symbol,
  };
}
