part of '../../imports.dart';

class TenantProfileCubit extends AsyncCubit<TenantProfileContent> {
  TenantProfileCubit() : super(const TenantProfileContent.initial());

  Future<void> getProfile() async {
    await executeAsyncWithBaseModel(
      operation: () => baseCrudUseCase.call(
        CrudBaseParmas<TenantProfileContent>(
          api: ApiConstants.tenantProfile,
          httpRequestType: HttpRequestType.get,
          cacheKey: TenantProfileContent.cacheKey,
          mapper: (json) =>
              TenantProfileContent.fromJson(_profileJsonMap(json)),
          fromCacheJson: TenantProfileContent.fromJson,
          toJson: (profile) => profile.toJson(),
        ),
      ),
      withInternetInterceptor: true,
    );
  }

  void updateFromUser(UserModel user) {
    updateData(
      data.copyWith(
        user: data.user.copyWith(fullName: user.name),
        accountDetails: data.accountDetails.copyWith(
          name: user.name,
          email: user.email,
        ),
      ),
    );
  }
}
