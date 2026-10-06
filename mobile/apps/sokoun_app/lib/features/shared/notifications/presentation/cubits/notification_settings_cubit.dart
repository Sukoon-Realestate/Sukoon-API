import 'package:melos_core/core/base_crud/code/domain/base_domain_imports.dart';
import 'package:melos_core/core/base_crud/code/presentation/cubit/base_cubit/async_cubit.dart';
import 'package:melos_core/core/network/api_endpoints.dart';

import '../../data/models/notification_setting_content.dart';

class NotificationSettingsCubit
    extends AsyncCubit<NotificationSettingsContent> {
  NotificationSettingsCubit()
    : super(const NotificationSettingsContent.initial());

  Future<void> loadSettings() async {
    if (isClosed || isLoading) return;
    await executeAsyncWithBaseModel(
      operation: () => baseCrudUseCase.call(
        CrudBaseParmas<NotificationSettingsContent>(
          api: ApiConstants.notificationSettings,
          httpRequestType: HttpRequestType.get,
          cacheKey: 'notification_settings',
          mapper: (json) => NotificationSettingsContent.fromJson(
            json is Map<String, dynamic> ? json : const {},
          ),
          fromCacheJson: NotificationSettingsContent.fromJson,
          toJson: (settings) => settings.toJson(),
        ),
      ),
      withInternetInterceptor: true,
    );
  }

  void updateSetting(String key, bool value) {
    updateData(data.updateValue(key, value));
  }
}

class NotificationSettingUpdateCubit extends AsyncCubit<String> {
  NotificationSettingUpdateCubit() : super('');

  Future<bool> updateSetting({required String key, required bool value}) async {
    if (isClosed || isLoading) return false;
    updateData(key);
    bool succeeded = false;
    await executeAsyncWithBaseModel(
      operation: () => baseCrudUseCase.call(
        CrudBaseParmas<String>(
          api: ApiConstants.notificationSettings,
          httpRequestType: HttpRequestType.patch,
          body: {key: value},
          mapper: (_) => key,
        ),
      ),
      onSuccess: (_) => succeeded = true,
    );
    return succeeded;
  }
}
