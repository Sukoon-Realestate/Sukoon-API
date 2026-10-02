import 'dart:async';
import 'dart:math' show max;

import 'package:melos_core/core/base_crud/code/domain/base_domain_imports.dart';
import 'package:melos_core/core/base_crud/code/presentation/cubit/base_cubit/async_cubit.dart';
import 'package:melos_core/core/network/account_session.dart';
import 'package:melos_core/core/network/api_endpoints.dart';
import 'package:melos_core/core/shared/models/user_models/user_model.dart';

import '../../../../main_view/data/enums/app_workspace.dart';
import '../../../../main_view/data/workspace_counts_refresh_bus.dart';
import '../../../notifications/data/enums/app_notification_kind.dart';
import '../../../notifications/data/foreground_notification_bus.dart';
import '../../../notifications/data/models/app_notification_content.dart';
import '../../../notifications/data/notification_refresh_bus.dart';
import '../../data/models/unread_counts.dart';

class UnreadCountsCubit extends AsyncCubit<UnreadCounts> {
  UnreadCountsCubit({this.workspace = AppWorkspace.tenant})
    : super(const UnreadCounts.initial());

  final AppWorkspace workspace;
  StreamSubscription<void>? _workspaceRefreshSubscription;
  StreamSubscription<void>? _notificationRefreshSubscription;
  StreamSubscription<AppNotificationContent>? _notificationSubscription;

  Future<void>? _loadRequest;
  int _sessionGeneration = AccountSession.generation;
  int _chatChange = 0;
  int _notificationsChange = 0;
  int _visitsChange = 0;
  bool _refreshPending = false;

  void watch() {
    if (isClosed) return;
    _workspaceRefreshSubscription ??= WorkspaceCountsRefreshBus.stream.listen(
      (_) => unawaited(refresh()),
    );
    if (workspace.isTenant) {
      _notificationRefreshSubscription ??= NotificationRefreshBus.stream.listen(
        (_) => unawaited(refresh()),
      );
    }
    _notificationSubscription ??= ForegroundNotificationBus.stream.listen(
      _onNotificationReceived,
    );
  }

  void _onNotificationReceived(AppNotificationContent notification) {
    if (!_canUpdate) return;
    if (workspace.isTenant) changeNotificationsCount(1);
    // Tenant visits already include pending bookings, so acceptance adds none.
    final int delta = switch (notification.kind) {
      AppNotificationKind.visitRequest when workspace.isOwner => 1,
      AppNotificationKind.visitRejected when workspace.isTenant => -1,
      _ => 0,
    };
    if (delta != 0) changeVisitsCount(delta);
  }

  Future<void> load() {
    if (isClosed ||
        !UserModel.isAuthenticated ||
        AccountSession.userId == null) {
      return Future.value();
    }
    if (_sessionGeneration != AccountSession.generation) {
      _sessionGeneration = AccountSession.generation;
      _loadRequest = null;
      _chatChange = 0;
      _notificationsChange = 0;
      _visitsChange = 0;
      _refreshPending = false;
      updateData(const UnreadCounts.initial());
      reset();
    }
    watch();
    return _loadRequest ??= _load();
  }

  Future<void> refresh() {
    if (_loadRequest != null &&
        _sessionGeneration == AccountSession.generation) {
      _refreshPending = true;
    }
    return load();
  }

  Future<void> _load() async {
    final int generation = _sessionGeneration;
    try {
      do {
        _refreshPending = false;
        final int chatChange = _chatChange;
        final int notificationsChange = _notificationsChange;
        final int visitsChange = _visitsChange;
        await executeAsyncWithBaseModel(
          operation: () => baseCrudUseCase.call(
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
              ),
              fromCacheJson: UnreadCounts.fromJson,
              toJson: (counts) => counts.toJson(),
            ),
          ),
          onSuccess: (_) => updateData(
            data.copyWith(
              chat: data.chat.copyWith(
                count: max(0, data.chat.count + _chatChange - chatChange),
              ),
              notifications: data.notifications.copyWith(
                count: max(
                  0,
                  data.notifications.count +
                      _notificationsChange -
                      notificationsChange,
                ),
              ),
              workspace: data.workspace.copyWith(
                visits: max(
                  0,
                  data.workspace.visits + _visitsChange - visitsChange,
                ),
              ),
            ),
          ),
          withInternetInterceptor: true,
        );
      } while (_refreshPending &&
          !isClosed &&
          generation == AccountSession.generation);
    } finally {
      if (generation == _sessionGeneration) _loadRequest = null;
    }
  }

  bool get _canUpdate =>
      !isClosed &&
      UserModel.isAuthenticated &&
      _sessionGeneration == AccountSession.generation;

  void changeChatCount(int delta) {
    if (!_canUpdate) return;
    _chatChange += delta;
    updateData(
      data.copyWith(
        chat: data.chat.copyWith(count: max(0, data.chat.count + delta)),
      ),
    );
  }

  void changeNotificationsCount(int delta) {
    if (!_canUpdate) return;
    _notificationsChange += delta;
    updateData(
      data.copyWith(
        notifications: data.notifications.copyWith(
          count: max(0, data.notifications.count + delta),
        ),
      ),
    );
  }

  void changeVisitsCount(int delta) {
    if (!_canUpdate) return;
    _visitsChange += delta;
    updateData(
      data.copyWith(
        workspace: data.workspace.copyWith(
          visits: max(0, data.workspace.visits + delta),
        ),
      ),
    );
  }

  @override
  Future<void> close() async {
    await _workspaceRefreshSubscription?.cancel();
    await _notificationRefreshSubscription?.cancel();
    await _notificationSubscription?.cancel();
    return super.close();
  }
}
