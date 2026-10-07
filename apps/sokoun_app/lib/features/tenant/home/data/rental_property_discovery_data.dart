import 'package:melos_core/config/language/locale_keys.g.dart';
import 'models/property_search_model.dart';

/// A v1 discovery page contains physical properties and server-filtered offer
/// summaries. Never deduplicate offer rows or manufacture property totals.
abstract final class RentalPropertyDiscoveryData {
  static PropertySearchResponseModel read(
    Map<String, dynamic> json,
    PropertySearchFilters filters,
  ) {
    final Object? count = json['count'];
    final Object? results = json['results'];
    if (count is! int ||
        count < 0 ||
        results is! List ||
        results.any((item) => item is! Map<String, dynamic>)) {
      throw FormatException(LocaleKeys.rentalDiscoveryIncompatible);
    }
    final page = PropertySearchResponseModel.fromJson(json);
    final ids = page.results.map((item) => item.id).toList();
    final int offset = (filters.page - 1) * filters.pageSize;
    final bool hasNext = page.next?.trim().isNotEmpty == true;
    if (ids.any((id) => id.isEmpty) ||
        ids.toSet().length != ids.length ||
        ids.length > filters.pageSize ||
        count < offset + ids.length ||
        (ids.isEmpty && count > offset) ||
        hasNext != (count > offset + ids.length) ||
        (filters.rentalScope.isNotEmpty &&
            page.results.any(
              (item) =>
                  item.rentalSummary?.matchesContext(
                    scope: filters.rentalScope,
                    period: filters.pricePeriod,
                  ) !=
                  true,
            ))) {
      throw FormatException(LocaleKeys.rentalDiscoveryIncompatible);
    }
    return page;
  }
}
