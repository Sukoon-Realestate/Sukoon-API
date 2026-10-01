part of '../../imports.dart';

class UserProfileCubit extends AsyncCubit<UserProfileContent> {
  UserProfileCubit() : super(const UserProfileContent.initial());
  Future<void> load({
    required void Function(UserProfileContent) onLoaded,
  }) async {
    if (isClosed || isLoading) return;
    await executeAsyncWithBaseModel(
      operation: () => baseCrudUseCase.call(
        CrudBaseParmas<UserProfileContent>(
          api: ApiConstants.userProfile,
          httpRequestType: HttpRequestType.get,
          cacheKey: 'editable_user_profile',
          mapper: (json) => UserProfileContent.fromJson(_profileJsonMap(json)),
          fromCacheJson: UserProfileContent.fromJson,
          toJson: (data) => data.toJson(),
        ),
      ),
      onSuccess: (response) => onLoaded(response.data),
      withInternetInterceptor: true,
    );
  }
}
