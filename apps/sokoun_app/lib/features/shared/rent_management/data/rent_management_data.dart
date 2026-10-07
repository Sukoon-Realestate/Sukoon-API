import 'package:pagify/helpers/data_and_pagination_data.dart';
import 'package:pagify/helpers/errors.dart';
import 'package:melos_core/config/language/locale_keys.g.dart';
import 'package:melos_core/core/network/account_session.dart';
import 'package:sokoun_app/features/shared/premium/data/premium_api_constants.dart';
import 'package:sokoun_app/features/shared/premium/data/premium_api_data.dart';
import 'package:sokoun_app/features/shared/premium/data/premium_json.dart';
import 'package:sokoun_app/features/main_view/data/enums/app_workspace.dart';
import 'models/rent_invoice.dart';

abstract final class RentManagementData {
  static String cacheKey(AppWorkspace workspace, {String leaseId = ''}) =>
      AccountSession.cacheKey(
        premiumCacheKey('invoices', [workspace.name, leaseId]),
      );
  static Future<(List<RentInvoice>, PaginationData)> getPage({
    required int page,
    required AppWorkspace workspace,
    String leaseId = '',
  }) async {
    final result = await PremiumApiData.page(
      endpoint: PremiumApiConstants.invoices,
      page: page,
      fromJson: RentInvoice.fromJson,
      query: {
        'workspace': workspace.name,
        if (leaseId.isNotEmpty) 'lease_id': leaseId,
      },
    );
    if (leaseId.isNotEmpty &&
        result.$1.any((invoice) => invoice.leaseId != leaseId)) {
      throw PagifyApiRequestException.initial().copyWith(
        msg: LocaleKeys.paidInvalidResponse,
      );
    }
    return result;
  }
}
