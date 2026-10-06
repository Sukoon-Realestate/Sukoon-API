import 'package:pagify/helpers/data_and_pagination_data.dart';
import 'package:melos_core/core/network/account_session.dart';
import 'package:sokoun_app/features/shared/premium/data/premium_api_constants.dart';
import 'package:sokoun_app/features/shared/premium/data/premium_api_data.dart';
import 'package:sokoun_app/features/shared/premium/data/premium_json.dart';
import 'models/promotion_campaign.dart';

abstract final class PromotionsData {
  static String get cacheKey =>
      AccountSession.cacheKey(premiumCacheKey('campaigns', []));
  static Future<(List<PromotionCampaign>, PaginationData)> getPage({
    required int page,
  }) => PremiumApiData.page(
    endpoint: PremiumApiConstants.campaigns,
    page: page,
    fromJson: PromotionCampaign.fromJson,
    query: {},
  );
}
