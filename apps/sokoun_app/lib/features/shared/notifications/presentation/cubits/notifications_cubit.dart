import 'package:melos_core/core/base_crud/code/domain/base_domain_imports.dart';
import 'package:melos_core/core/base_crud/code/presentation/cubit/base_cubit/async_cubit.dart';
import 'package:melos_core/core/network/api_endpoints.dart';

import '../../data/models/notification_operations_state.dart';
import '../../data/notification_refresh_bus.dart';

class NotificationsCubit extends AsyncCubit<NotificationOperationsState> {
  NotificationsCubit() : super(const NotificationOperationsState.initial());

  void setUnreadCount(int count) {
    updateData(data.copyWith(unreadCount: count < 0 ? 0 : count));
  }

  Future<bool> markAsRead(String notificationId) async {
    if (isClosed ||
        notificationId.isEmpty ||
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
    if (isClosed || data.isMarkingAll || data.unreadCount == 0) return false;

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
