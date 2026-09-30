import 'dart:async';

import 'package:melos_core/core/base_crud/code/domain/base_domain_imports.dart';
import 'package:melos_core/core/base_crud/code/presentation/cubit/base_cubit/async_cubit.dart';
import 'package:melos_core/core/network/api_endpoints.dart';
import 'package:melos_core/core/network/account_session.dart';

import '../../data/foreground_notification_bus.dart';
import '../../data/models/app_notification_content.dart';
import '../../data/models/unread_notifications_content.dart';
import '../../data/notification_refresh_bus.dart';
import '../../data/notifications_data.dart';

class UnreadNotificationsCubit extends AsyncCubit<UnreadNotificationsContent> {
  UnreadNotificationsCubit()
    : super(const UnreadNotificationsContent.initial());

  StreamSubscription<void>? _refreshSubscription;
  StreamSubscription<AppNotificationContent>? _notificationSubscription;
  int _sessionGeneration = AccountSession.generation;
  int _notificationsChange = 0;

  Future<void> loadUnreadCount() async {
    if (isClosed || isLoading) return;
    if (!await NotificationsData.hasAuthenticatedSession()) return;
    if (isClosed || isLoading) return;
    _sessionGeneration = AccountSession.generation;
    final int notificationsChangeAtRequest = _notificationsChange;
    await executeAsyncWithBaseModel(
      operation: () => baseCrudUseCase.call(
        CrudBaseParmas<UnreadNotificationsContent>(
          api: ApiConstants.tenantUnreadCounts,
          httpRequestType: HttpRequestType.get,
          cacheKey: 'notifications_unread_count_v2',
          mapper: (json) => UnreadNotificationsContent.fromJson(
            json is Map<String, dynamic> ? json : const {},
          ),
          fromCacheJson: UnreadNotificationsContent.fromJson,
          toJson: (count) => count.toJson(),
        ),
      ),
      onSuccess: (_) {
        final int delta = _notificationsChange - notificationsChangeAtRequest;
        if (delta != 0) updateData(data.copyWith(count: data.count + delta));
      },
      withInternetInterceptor: true,
    );
  }

  void watchRefreshRequests() {
    _refreshSubscription ??= NotificationRefreshBus.stream.listen(
      (_) => loadUnreadCount(),
    );
    _notificationSubscription ??= ForegroundNotificationBus.stream.listen((_) {
      if (isClosed || _sessionGeneration != AccountSession.generation) return;
      _notificationsChange++;
      updateData(data.copyWith(count: data.count + 1));
    });
  }

  @override
  Future<void> close() async {
    await _refreshSubscription?.cancel();
    await _notificationSubscription?.cancel();
    return super.close();
  }
}
