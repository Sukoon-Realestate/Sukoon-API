import 'package:melos_core/core/base_crud/code/domain/base_domain_imports.dart';
import 'package:melos_core/core/network/api_endpoints.dart';

import 'models/account_content.dart';
import 'profile_json.dart';

abstract final class AccountData {
  static CrudBaseParmas<AccountContent> request({required bool cacheProfile}) =>
      CrudBaseParmas<AccountContent>(
        api: ApiConstants.getAccData,
        httpRequestType: HttpRequestType.get,
        // Only an established identity may read its account cache.
        cacheKey: cacheProfile ? AccountContent.cacheKey : null,
        mapper: (json) {
          final AccountContent account = AccountContent.fromJson(
            profileJsonMap(json),
          );
          if (account.user.id.isEmpty || account.user.id == '0') {
            throw const FormatException('Missing authenticated account ID');
          }
          return account;
        },
        fromCacheJson: AccountContent.fromJson,
        toJson: (account) => account.toJson(),
      );
}
