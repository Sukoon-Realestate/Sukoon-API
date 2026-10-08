import 'package:melos_core/core/network/account_session.dart';
import 'package:pagify/helpers/data_and_pagination_data.dart';
import 'package:sokoun_app/features/shared/premium/data/premium_api_constants.dart';
import 'package:sokoun_app/features/shared/premium/data/premium_api_data.dart';
import 'package:sokoun_app/features/shared/premium/data/premium_json.dart';
import 'models/lease_tenant.dart';
import '../../tenancy_invitations/data/tenancy_invitation_capabilities.dart';

abstract final class LeaseTenantsData {
  static String cacheKey(String propertyId, {String offerId = ''}) =>
      AccountSession.cacheKey(
        premiumCacheKey('lease_tenants', [
          propertyId,
          offerId,
          TenancyInvitationCapabilities.current.enabled,
        ]),
      );
  static Future<(List<LeaseTenant>, PaginationData)> getPage({
    required String propertyId,
    required int page,
    String offerId = '',
  }) => PremiumApiData.page(
    endpoint: PremiumApiConstants.leaseTenants,
    page: page,
    query: {
      'property_id': propertyId,
      if (offerId.isNotEmpty && TenancyInvitationCapabilities.current.enabled)
        'offer_id': offerId,
    },
    fromJson: LeaseTenant.fromJson,
  );
}
