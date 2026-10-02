import 'dart:async';
import 'dart:math' show max;

import 'package:melos_core/core/base_crud/code/domain/usecases/pagination_response.dart';
import 'package:melos_core/core/base_crud/code/presentation/cubit/base_cubit/async_cubit.dart';
import 'package:melos_core/core/error/failure.dart';
import 'package:melos_core/core/network/account_session.dart';
import 'package:melos_core/core/shared/models/user_models/user_model.dart';
import 'package:multiple_result/multiple_result.dart';

import '../../../../main_view/data/enums/app_workspace.dart';
import '../../../../main_view/data/workspace_counts_refresh_bus.dart';
import '../../../chat/data/chat_realtime_service.dart';
import '../../../chat/data/chat_unread_refresh_bus.dart';
import '../../../chat/data/models/chat_socket_message.dart';
import '../../../notifications/data/enums/app_notification_kind.dart';
import '../../../notifications/data/foreground_notification_bus.dart';
import '../../../notifications/data/models/app_notification_content.dart';
import '../../../notifications/data/notification_refresh_bus.dart';
import '../../data/models/unread_counts.dart';
import '../../data/unread_counts_data.dart';

/// Owns all account badges, including both workspace snapshots and live deltas.
class UnreadCountsCubit extends AsyncCubit<UnreadCounts> {
  UnreadCountsCubit({ChatRealtimeGateway? realtimeService})
    : _realtime = realtimeService ?? ChatRealtimeService.instance,
      super(const UnreadCounts.initial());

  final ChatRealtimeGateway _realtime;
  final List<StreamSubscription<dynamic>> _subscriptions = [];
  final Map<AppWorkspace, Future<void>> _requests = {};
  final Set<AppWorkspace> _pendingRefreshes = {};
  final Map<AppWorkspace, int> _visitsChanges = {};
  final Set<String> _receivedMessageIds = {};
  int _sessionGeneration = AccountSession.generation;
  int _chatChange = 0;
  int _notificationsChange = 0;

  void watch() {
    if (isClosed || _subscriptions.isNotEmpty) return;
    _subscriptions.addAll([
      WorkspaceCountsRefreshBus.stream.listen((_) => unawaited(refresh())),
      NotificationRefreshBus.stream.listen(
        (_) => unawaited(refresh(workspace: AppWorkspace.tenant)),
      ),
      ForegroundNotificationBus.stream.listen(_onNotificationReceived),
      _realtime.messages.listen(_onMessageReceived),
      ChatUnreadRefreshBus.stream.listen((removed) {
        if (!_canUpdate) return;
        changeChatCount(-removed);
        if (removed == 0) {
          unawaited(refresh(workspace: AppWorkspace.tenant));
        }
      }),
    ]);
  }

  Future<void> load({AppWorkspace? workspace}) {
    if (isClosed ||
        !UserModel.isAuthenticated ||
        AccountSession.userId == null) {
      return Future<void>.value();
    }
    if (_sessionGeneration != AccountSession.generation) {
      _sessionGeneration = AccountSession.generation;
      _requests.clear();
      _pendingRefreshes.clear();
      _visitsChanges.clear();
      _receivedMessageIds.clear();
      _chatChange = 0;
      _notificationsChange = 0;
      updateData(const UnreadCounts.initial());
      reset();
    }
    watch();
    final int generation = _sessionGeneration;
    final Iterable<AppWorkspace> workspaces = workspace == null
        ? AppWorkspace.values
        : [workspace];
    return Future.wait<void>(
      workspaces.map(
        (role) => _requests.putIfAbsent(
          role,
          () => _loadWorkspace(role, generation).whenComplete(() {
            if (generation == _sessionGeneration) _requests.remove(role);
          }),
        ),
      ),
    ).then((_) {});
  }

  Future<void> refresh({AppWorkspace? workspace}) {
    if (_sessionGeneration == AccountSession.generation) {
      _pendingRefreshes.addAll(
        _requests.keys.where((role) => workspace == null || role == workspace),
      );
    }
    return load(workspace: workspace);
  }

  Future<void> _loadWorkspace(AppWorkspace workspace, int generation) async {
    do {
      _pendingRefreshes.remove(workspace);
      final int chatChange = _chatChange;
      final int notificationsChange = _notificationsChange;
      final int visitsChange = _visitsChanges[workspace] ?? 0;
      await executeAsyncWithBaseModel(
        operation: () async {
          final result = await UnreadCountsData.load(workspace);
          return result.when(
            (response) => Success<BaseModel<UnreadCounts>, Failure>(
              BaseModel<UnreadCounts>(
                key: response.key,
                msg: response.msg,
                data: _mergeSnapshot(
                  workspace: workspace,
                  snapshot: response.data,
                  chatChange: chatChange,
                  notificationsChange: notificationsChange,
                  visitsChange: visitsChange,
                ),
              ),
            ),
            (failure) => Error<BaseModel<UnreadCounts>, Failure>(failure),
          );
        },
        shouldApplyResult: () => generation == _sessionGeneration,
        withInternetInterceptor: true,
      );
    } while (generation == _sessionGeneration &&
        _pendingRefreshes.contains(workspace) &&
        _canUpdate);
  }

  UnreadCounts _mergeSnapshot({
    required AppWorkspace workspace,
    required UnreadCounts snapshot,
    required int chatChange,
    required int notificationsChange,
    required int visitsChange,
  }) {
    final counts = snapshot.forWorkspace(workspace);
    final updated = counts.copyWith(
      visits: max(
        0,
        counts.visits + (_visitsChanges[workspace] ?? 0) - visitsChange,
      ),
    );
    if (workspace.isOwner) return data.copyWith(owner: updated);
    return data.copyWith(
      tenant: updated,
      chatCount: max(0, snapshot.chatCount + _chatChange - chatChange),
      notificationsCount: max(
        0,
        snapshot.notificationsCount +
            _notificationsChange -
            notificationsChange,
      ),
    );
  }

  bool get _canUpdate =>
      !isClosed &&
      UserModel.isAuthenticated &&
      _sessionGeneration == AccountSession.generation;

  void changeChatCount(int delta) {
    if (!_canUpdate || delta == 0) return;
    _chatChange += delta;
    updateData(data.copyWith(chatCount: max(0, data.chatCount + delta)));
  }

  void changeNotificationsCount(int delta) {
    if (!_canUpdate || delta == 0) return;
    _notificationsChange += delta;
    updateData(
      data.copyWith(
        notificationsCount: max(0, data.notificationsCount + delta),
      ),
    );
  }

  void changeVisitsCount({
    required AppWorkspace workspace,
    required int delta,
  }) {
    if (!_canUpdate || delta == 0) return;
    _visitsChanges[workspace] = (_visitsChanges[workspace] ?? 0) + delta;
    final counts = data.forWorkspace(workspace);
    final updated = counts.copyWith(visits: max(0, counts.visits + delta));
    updateData(
      workspace.isOwner
          ? data.copyWith(owner: updated)
          : data.copyWith(tenant: updated),
    );
  }

  void _onNotificationReceived(AppNotificationContent notification) {
    if (!_canUpdate) return;
    changeNotificationsCount(1);
    // Pending tenant bookings already include accepted requests.
    if (notification.kind == AppNotificationKind.visitRequest) {
      changeVisitsCount(workspace: AppWorkspace.owner, delta: 1);
    } else if (notification.kind == AppNotificationKind.visitRejected) {
      changeVisitsCount(workspace: AppWorkspace.tenant, delta: -1);
    }
    if (notification.kind == AppNotificationKind.newMessage ||
        notification.category == 'chat') {
      _addUnreadMessage(
        messageId: notification.payload.messageId,
        conversationId: notification.payload.chatId,
        senderId: notification.payload.senderId,
      );
    }
  }

  void _onMessageReceived(ChatSocketMessage message) => _addUnreadMessage(
    messageId: message.id,
    conversationId: message.conversationId,
    senderId: message.sender.id,
  );

  void _addUnreadMessage({
    required String messageId,
    required String conversationId,
    required String senderId,
  }) {
    if (!_canUpdate) return;
    if (messageId.isNotEmpty) {
      if (!_receivedMessageIds.add(messageId)) return;
      if (_receivedMessageIds.length > 200) {
        _receivedMessageIds.remove(_receivedMessageIds.first);
      }
    }
    if (senderId == UserModel.currentUser?.id ||
        conversationId == _realtime.activeConversationId) {
      return;
    }
    changeChatCount(1);
  }

  @override
  Future<void> close() => Future.wait<void>([
    super.close(),
    ..._subscriptions.map((subscription) => subscription.cancel()),
  ]);
}
