import 'package:pagify/helpers/data_and_pagination_data.dart';
import 'package:pagify/helpers/errors.dart';
import 'package:melos_core/config/language/locale_keys.g.dart';
import 'package:melos_core/core/network/account_session.dart';
import 'package:sokoun_app/features/shared/premium/data/premium_api_constants.dart';
import 'package:sokoun_app/features/shared/premium/data/premium_api_data.dart';
import 'package:sokoun_app/features/shared/premium/data/premium_json.dart';
import 'package:sokoun_app/features/main_view/data/enums/app_workspace.dart';
import 'models/digital_lease.dart';

abstract final class DigitalLeasesData {
  static String cacheKey(AppWorkspace workspace, {String propertyId = ''}) =>
      AccountSession.cacheKey(
        premiumCacheKey('leases', [workspace.name, propertyId]),
      );
  static Future<(List<DigitalLease>, PaginationData)> getPage({
    required int page,
    required AppWorkspace workspace,
    String propertyId = '',
  }) async {
    final result = await PremiumApiData.page(
      endpoint: PremiumApiConstants.leases,
      page: page,
      fromJson: DigitalLease.fromJson,
      query: {
        'workspace': workspace.name,
        if (propertyId.isNotEmpty) 'property_id': propertyId,
      },
    );
    if (propertyId.isNotEmpty &&
        result.$1.any((lease) => lease.propertyId != propertyId)) {
      throw PagifyApiRequestException.initial().copyWith(
        msg: LocaleKeys.paidInvalidResponse,
      );
    }
    return result;
  }
}
