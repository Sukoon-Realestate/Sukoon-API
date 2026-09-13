import 'package:melos_core/core/base_crud/code/domain/base_domain_imports.dart';
import 'package:melos_core/core/base_crud/code/presentation/cubit/base_cubit/async_cubit.dart';
import 'package:melos_core/core/base_crud/code/domain/usecases/pagination_response.dart';
import 'package:melos_core/core/network/api_endpoints.dart';

import '../../data/models/app_notification_content.dart';
import '../../data/notification_refresh_bus.dart';

class NotificationDetailCubit extends AsyncCubit<AppNotificationContent> {
  NotificationDetailCubit({AppNotificationContent? initialNotification})
    : super(initialNotification ?? const AppNotificationContent.initial());

  Future<void> load({
    required String notificationId,
    AppNotificationContent? fixture,
  }) async {
    if (fixture != null) {
      setSuccess(BaseModel(key: '', msg: '', data: fixture));
      return;
    }

    await executeAsyncWithBaseModel(
      operation: () => baseCrudUseCase.call(
        CrudBaseParmas<AppNotificationContent>(
          api: ApiConstants.notificationDetails(notificationId),
          httpRequestType: HttpRequestType.get,
          cacheKey: 'notification_details_$notificationId',
          mapper: (json) => AppNotificationContent.fromJson(
            json is Map<String, dynamic> ? json : const {},
          ),
          fromCacheJson: AppNotificationContent.fromJson,
          toJson: (notification) => notification.toJson(),
        ),
      ),
      onSuccess: (_) => NotificationRefreshBus.requestRefresh(),
      withInternetInterceptor: true,
    );
  }
}
