import 'package:melos_core/config/res/config_imports.dart';
import 'package:melos_core/core/base_crud/code/domain/base_domain_imports.dart';
import 'package:melos_core/core/base_crud/code/domain/usecases/pagination_response.dart';
import 'package:melos_core/core/error/failure.dart';
import 'package:melos_core/core/network/api_endpoints.dart';
import 'package:multiple_result/multiple_result.dart';

import '../../../main_view/data/enums/app_workspace.dart';
import 'models/unread_counts.dart';

abstract final class UnreadCountsData {
  static Future<Result<BaseModel<UnreadCounts>, Failure>> load(
    AppWorkspace workspace,
  ) => injector<BaseCrudUseCase>().call(
    CrudBaseParmas<UnreadCounts>(
      api: workspace.isOwner
          ? ApiConstants.ownerUnreadCounts
          : ApiConstants.tenantUnreadCounts,
      httpRequestType: HttpRequestType.get,
      cacheKey: workspace.isOwner
          ? 'workspace_counts_owner'
          : 'tenant_unread_counts',
      mapper: (json) => UnreadCounts.fromJson(
        json is Map ? Map<String, dynamic>.from(json) : const {},
        workspace: workspace,
      ),
      fromCacheJson: (json) =>
          UnreadCounts.fromJson(json, workspace: workspace),
      toJson: (counts) => counts.toJson(),
    ),
  );
}
