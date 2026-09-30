import 'dart:async';
import 'package:melos_core/core/base_crud/code/domain/base_domain_imports.dart';
import 'package:melos_core/core/base_crud/code/presentation/cubit/base_cubit/async_cubit.dart';
import 'package:melos_core/core/network/api_endpoints.dart';
import 'package:melos_core/core/shared/models/user_models/user_model.dart';
import '../../data/enums/app_workspace.dart';
import '../../data/models/workspace_counts.dart';
import '../../data/workspace_counts_refresh_bus.dart';

class WorkspaceCountsCubit extends AsyncCubit<WorkspaceCounts> {
  WorkspaceCountsCubit(this.workspace) : super(const WorkspaceCounts.initial());
  final AppWorkspace workspace;
  StreamSubscription<void>? _subscription;
  bool _reload = false;

  void watch() {
    _subscription ??= WorkspaceCountsRefreshBus.stream.listen((_) => load());
  }

  Future<void> load() async {
    if (isClosed || !UserModel.isAuthenticated) return;
    if (isLoading) {
      _reload = true;
      return;
    }
    await executeAsyncWithBaseModel(
      operation: () => baseCrudUseCase.call(
        CrudBaseParmas<WorkspaceCounts>(
          api: workspace.isOwner
              ? ApiConstants.ownerUnreadCounts
              : ApiConstants.tenantUnreadCounts,
          httpRequestType: HttpRequestType.get,
          cacheKey: 'workspace_counts_${workspace.name}',
          mapper: (json) =>
              WorkspaceCounts.fromJson(Map<String, dynamic>.from(json as Map)),
          fromCacheJson: WorkspaceCounts.fromJson,
          toJson: (counts) => counts.toJson(),
        ),
      ),
      withInternetInterceptor: true,
    );
    if (_reload && !isClosed) {
      _reload = false;
      await load();
    }
  }

  @override
  Future<void> close() async {
    await _subscription?.cancel();
    return super.close();
  }
}
