import 'package:pagify/helpers/data_and_pagination_data.dart';
import 'package:melos_core/core/network/account_session.dart';
import 'package:sokoun_app/features/shared/premium/data/premium_api_constants.dart';
import 'package:sokoun_app/features/shared/premium/data/premium_api_data.dart';
import 'package:sokoun_app/features/shared/premium/data/premium_json.dart';
import 'models/premium_search_alert.dart';

abstract final class PremiumAlertsData {
  static String get cacheKey =>
      AccountSession.cacheKey(premiumCacheKey('alerts', []));
  static Future<(List<PremiumSearchAlert>, PaginationData)> getPage({
    required int page,
  }) => PremiumApiData.page(
    endpoint: PremiumApiConstants.alerts,
    page: page,
    fromJson: PremiumSearchAlert.fromJson,
    query: {},
  );
}
