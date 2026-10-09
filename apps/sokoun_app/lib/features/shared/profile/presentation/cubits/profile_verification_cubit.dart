part of '../../imports.dart';

class ProfileVerificationCubit extends AsyncCubit<ProfileVerificationContent> {
  ProfileVerificationCubit()
    : super(const ProfileVerificationContent.initial());
  Future<void> load() async {
    if (isClosed || isLoading) return;
    await executeAsyncWithBaseModel(
      operation: () => baseCrudUseCase.call(
        CrudBaseParmas<ProfileVerificationContent>(
          api: ApiConstants.verificationStatus,
          httpRequestType: HttpRequestType.get,
          cachePolicy: ReadCachePolicy.privateMemory,
          cacheKey: 'profile_verification_status_v1',
          mapper: (json) =>
              ProfileVerificationContent.fromJson(profileJsonMap(json)),
          fromCacheJson: ProfileVerificationContent.fromJson,
          toJson: (data) => data.toJson(),
        ),
      ),
      withInternetInterceptor: true,
    );
  }
}
