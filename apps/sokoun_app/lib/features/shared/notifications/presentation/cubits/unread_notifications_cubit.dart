import 'dart:async';

import 'package:melos_core/core/base_crud/code/domain/base_domain_imports.dart';
import 'package:melos_core/core/base_crud/code/presentation/cubit/base_cubit/async_cubit.dart';
import 'package:melos_core/core/network/api_endpoints.dart';

import '../../data/models/unread_notifications_content.dart';
import '../../data/notification_refresh_bus.dart';
import '../../data/notifications_data.dart';

class UnreadNotificationsCubit extends AsyncCubit<UnreadNotificationsContent> {
  UnreadNotificationsCubit()
    : super(const UnreadNotificationsContent.initial());

  StreamSubscription<void>? _refreshSubscription;

  Future<void> loadUnreadCount() async {
    if (isLoading) return;
    if (!await NotificationsData.hasAuthenticatedSession()) return;
    if (isLoading) return;
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
      withInternetInterceptor: true,
    );
  }

  void watchRefreshRequests() {
    _refreshSubscription ??= NotificationRefreshBus.stream.listen(
      (_) => loadUnreadCount(),
    );
  }

  @override
  Future<void> close() async {
    await _refreshSubscription?.cancel();
    return super.close();
  }
}
