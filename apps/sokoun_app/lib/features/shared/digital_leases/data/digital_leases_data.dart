import 'package:pagify/helpers/data_and_pagination_data.dart';
import 'package:melos_core/core/network/account_session.dart';
import 'package:sokoun_app/features/shared/premium/data/premium_api_constants.dart';
import 'package:sokoun_app/features/shared/premium/data/premium_api_data.dart';
import 'package:sokoun_app/features/shared/premium/data/premium_json.dart';
import 'package:sokoun_app/features/main_view/data/enums/app_workspace.dart';
import 'models/digital_lease.dart';

abstract final class DigitalLeasesData {
  static String cacheKey(AppWorkspace workspace) =>
      AccountSession.cacheKey(premiumCacheKey('leases', [workspace.name]));
  static Future<(List<DigitalLease>, PaginationData)> getPage({
    required int page,
    required AppWorkspace workspace,
  }) => PremiumApiData.page(
    endpoint: PremiumApiConstants.leases,
    page: page,
    fromJson: DigitalLease.fromJson,
    query: {'workspace': workspace.name},
  );
}
