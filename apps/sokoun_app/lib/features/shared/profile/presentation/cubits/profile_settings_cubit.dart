part of '../../imports.dart';

class ProfileSettingsCubit extends AsyncCubit<ProfileSettingsContent> {
  ProfileSettingsCubit() : super(const ProfileSettingsContent.initial());
  Future<void> load() async {
    if (isClosed || isLoading) return;
    await executeAsyncWithBaseModel(
      operation: () => baseCrudUseCase.call(
        CrudBaseParmas<ProfileSettingsContent>(
          api: ApiConstants.profileSettings,
          httpRequestType: HttpRequestType.get,
          cachePolicy: ReadCachePolicy.privateMemory,
          cacheKey: 'profile_settings',
          mapper: (json) =>
              ProfileSettingsContent.fromJson(profileJsonMap(json)),
          fromCacheJson: ProfileSettingsContent.fromJson,
          toJson: (data) => data.toJson(),
        ),
      ),
      withInternetInterceptor: true,
    );
  }

  void apply(ProfileSetting setting, bool value) {
    updateData(data.copyWith(values: {...data.values, setting: value}));
  }
}

class ProfileSettingUpdateCubit extends AsyncCubit<ProfileSetting?> {
  ProfileSettingUpdateCubit() : super(null);
  final PreferenceWriteQueue _queue = PreferenceWriteQueue();
  bool desiredValue(ProfileSetting setting, bool fallback) =>
      _queue.valueFor(setting.apiKey, fallback);
  Future<bool> save(ProfileSetting setting, bool value, {bool? baseline}) =>
      _queue.update(
        key: setting.apiKey,
        baseline: baseline ?? !value,
        value: value,
        send: (key, value) => _send(
          ProfileSetting.values.firstWhere((entry) => entry.apiKey == key),
          value,
        ),
      );
  Future<bool> _send(ProfileSetting setting, bool value) async {
    if (isClosed) return false;
    updateData(setting);
    bool succeeded = false;
    await executeAsyncWithBaseModel(
      operation: () => baseCrudUseCase.call(
        CrudBaseParmas<ProfileSetting?>(
          api: ApiConstants.profileSettings,
          httpRequestType: HttpRequestType.patch,
          body: {setting.apiKey: value},
          mapper: (_) => setting,
        ),
      ),
      onSuccess: (_) {
        ObjectBoxCacheService.remove('profile_settings');
        succeeded = true;
      },
    );
    return succeeded;
  }
}
