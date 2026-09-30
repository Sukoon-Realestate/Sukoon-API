import 'dart:async';
import 'dart:math' show max;
import 'package:melos_core/core/base_crud/code/domain/base_domain_imports.dart';
import 'package:melos_core/core/base_crud/code/presentation/cubit/base_cubit/async_cubit.dart';
import 'package:melos_core/core/network/api_endpoints.dart';
import 'package:melos_core/core/network/account_session.dart';
import 'package:melos_core/core/shared/models/user_models/user_model.dart';
import '../../../shared/notifications/data/enums/app_notification_kind.dart';
import '../../../shared/notifications/data/foreground_notification_bus.dart';
import '../../../shared/notifications/data/models/app_notification_content.dart';
import '../../data/enums/app_workspace.dart';
import '../../data/models/workspace_counts.dart';
import '../../data/workspace_counts_refresh_bus.dart';

class WorkspaceCountsCubit extends AsyncCubit<WorkspaceCounts> {
  WorkspaceCountsCubit(this.workspace) : super(const WorkspaceCounts.initial());
  final AppWorkspace workspace;
  StreamSubscription<void>? _subscription;
  StreamSubscription<AppNotificationContent>? _notificationSubscription;
  int _sessionGeneration = AccountSession.generation;
  int _visitsChange = 0;
  bool _reload = false;

  void watch() {
    _subscription ??= WorkspaceCountsRefreshBus.stream.listen((_) => load());
    _notificationSubscription ??= ForegroundNotificationBus.stream.listen(
      _onNotificationReceived,
    );
  }

  void _onNotificationReceived(AppNotificationContent notification) {
    if (isClosed || _sessionGeneration != AccountSession.generation) return;
    // Tenant visits already include pending bookings, so acceptance adds none.
    final int delta = switch (notification.kind) {
      AppNotificationKind.visitRequest when workspace.isOwner => 1,
      AppNotificationKind.visitRejected when workspace.isTenant => -1,
      _ => 0,
    };
    if (delta == 0) return;
    _visitsChange += delta;
    updateData(data.copyWith(visits: max(0, data.visits + delta)));
  }

  Future<void> load() async {
    if (isClosed || !UserModel.isAuthenticated) return;
    if (isLoading) {
      _reload = true;
      return;
    }
    _sessionGeneration = AccountSession.generation;
    final int visitsChangeAtRequest = _visitsChange;
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
      onSuccess: (_) {
        final int delta = _visitsChange - visitsChangeAtRequest;
        if (delta != 0) {
          updateData(data.copyWith(visits: max(0, data.visits + delta)));
        }
      },
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
    await _notificationSubscription?.cancel();
    return super.close();
  }
}
