import 'package:melos_core/core/base_crud/code/domain/base_domain_imports.dart';
import 'package:melos_core/core/base_crud/code/presentation/cubit/base_cubit/async_cubit.dart';
import 'package:melos_core/core/network/api_endpoints.dart';

import '../../data/models/notification_operations_state.dart';
import '../../data/notification_refresh_bus.dart';
import '../../data/notifications_data.dart';

class NotificationsCubit extends AsyncCubit<NotificationOperationsState> {
  NotificationsCubit() : super(const NotificationOperationsState.initial());

  void setUnreadCount(int count) {
    updateData(data.copyWith(unreadCount: count < 0 ? 0 : count));
  }

  Future<void> loadUnreadCount() async {
    if (!await NotificationsData.hasAuthenticatedSession()) return;
    await executeAsyncWithBaseModel(
      operation: () => baseCrudUseCase.call(
        CrudBaseParmas<NotificationOperationsState>(
          api: ApiConstants.unreadNotificationCount,
          httpRequestType: HttpRequestType.get,
          cacheKey: 'notifications_unread_count',
          mapper: (json) =>
              data.copyWith(unreadCount: _unreadCountFromJson(json)),
          fromCacheJson: NotificationOperationsState.fromJson,
          toJson: (state) => state.toJson(),
        ),
      ),
      withInternetInterceptor: true,
    );
  }

  Future<bool> markAsRead(String notificationId) async {
    if (notificationId.isEmpty ||
        data.pendingNotificationIds.contains(notificationId)) {
      return false;
    }

    final int previousUnreadCount = data.unreadCount;
    updateData(
      data.copyWith(
        unreadCount: previousUnreadCount > 0 ? previousUnreadCount - 1 : 0,
        pendingNotificationIds: {
          ...data.pendingNotificationIds,
          notificationId,
        },
      ),
    );

    bool succeeded = false;
    await executeAsyncWithBaseModel(
      operation: () => baseCrudUseCase.call(
        CrudBaseParmas<NotificationOperationsState>(
          api: ApiConstants.markNotificationRead(notificationId),
          httpRequestType: HttpRequestType.patch,
          mapper: (_) => data.copyWith(
            pendingNotificationIds: {...data.pendingNotificationIds}
              ..remove(notificationId),
          ),
        ),
      ),
      onSuccess: (_) {
        succeeded = true;
        NotificationRefreshBus.requestRefresh();
      },
      onError: (_) {
        updateData(
          data.copyWith(
            unreadCount: previousUnreadCount,
            pendingNotificationIds: {...data.pendingNotificationIds}
              ..remove(notificationId),
          ),
        );
      },
    );
    return succeeded;
  }

  Future<bool> markAllAsRead() async {
    if (data.isMarkingAll || data.unreadCount == 0) return false;

    final int previousUnreadCount = data.unreadCount;
    updateData(data.copyWith(isMarkingAll: true));
    bool succeeded = false;
    await executeAsyncWithBaseModel(
      operation: () => baseCrudUseCase.call(
        CrudBaseParmas<NotificationOperationsState>(
          api: ApiConstants.markAllNotificationsRead,
          httpRequestType: HttpRequestType.post,
          mapper: (_) => data.copyWith(unreadCount: 0, isMarkingAll: false),
        ),
      ),
      onSuccess: (_) {
        succeeded = true;
        NotificationRefreshBus.requestRefresh();
      },
      onError: (_) {
        updateData(
          data.copyWith(unreadCount: previousUnreadCount, isMarkingAll: false),
        );
      },
    );
    return succeeded;
  }
}

int _unreadCountFromJson(dynamic json) {
  if (json is! Map) return 0;
  return (json['unread_count'] as num?)?.toInt() ?? 0;
}
