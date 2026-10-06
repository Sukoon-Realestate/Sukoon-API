import 'package:melos_core/core/network/account_session.dart';
import 'package:pagify/helpers/data_and_pagination_data.dart';
import 'package:sokoun_app/features/shared/premium/data/premium_api_constants.dart';
import 'package:sokoun_app/features/shared/premium/data/premium_api_data.dart';
import 'package:sokoun_app/features/shared/premium/data/premium_json.dart';
import 'models/lease_tenant.dart';

abstract final class LeaseTenantsData {
  static String cacheKey(String propertyId) =>
      AccountSession.cacheKey(premiumCacheKey('lease_tenants', [propertyId]));
  static Future<(List<LeaseTenant>, PaginationData)> getPage({
    required String propertyId,
    required int page,
  }) => PremiumApiData.page(
    endpoint: PremiumApiConstants.leaseTenants,
    page: page,
    query: {'property_id': propertyId},
    fromJson: LeaseTenant.fromJson,
  );
}
