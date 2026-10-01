part of '../../imports.dart';

class TenantProfileCubit extends AsyncCubit<TenantProfileContent> {
  TenantProfileCubit() : super(const TenantProfileContent.initial());

  Future<void>? _profileRequest;

  /// The home account request also supplies this profile. Join it if the
  /// profile tab opens before account initialization has finished.
  void useAccountRequest(Future<void> request) {
    _profileRequest = request.whenComplete(() => _profileRequest = null);
  }

  void setProfile(TenantProfileContent profile) {
    ObjectBoxCacheService.save(TenantProfileContent.cacheKey, profile.toJson());
    emit(state.success(data: profile));
  }

  void restoreCachedProfile() {
    final Map<String, dynamic>? cached = ObjectBoxCacheService.read(
      TenantProfileContent.cacheKey,
    );
    if (cached != null) {
      emit(state.success(data: TenantProfileContent.fromJson(cached)));
    }
  }

  Future<void> getProfile() {
    if (isClosed) return Future<void>.value();
    return _profileRequest ??= _loadProfile().whenComplete(
      () => _profileRequest = null,
    );
  }

  Future<void> _loadProfile() async {
    await executeAsyncWithBaseModel(
      operation: () => baseCrudUseCase.call(
        CrudBaseParmas<TenantProfileContent>(
          api: ApiConstants.getAccData,
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
          phoneNumber: user.phone,
          maskedPhoneNumber: ProfileAccountDetailsContent.maskPhone(user.phone),
        ),
      ),
    );
  }
}
