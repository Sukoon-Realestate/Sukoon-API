part of '../../imports.dart';

class OwnerProfileCubit extends AsyncCubit<OwnerProfileContent> {
  OwnerProfileCubit() : super(const OwnerProfileContent.initial());

  Future<void> getProfile() async {
    if (isClosed || isLoading) return;
    await executeAsyncWithBaseModel(
      operation: () => baseCrudUseCase.call(
        CrudBaseParmas<OwnerProfileContent>(
          api: ApiConstants.ownerProfile,
          httpRequestType: HttpRequestType.get,
          cachePolicy: ReadCachePolicy.privateMemory,
          cacheKey: OwnerProfileContent.cacheKey,
          mapper: (json) => OwnerProfileContent.fromJson(profileJsonMap(json)),
          fromCacheJson: OwnerProfileContent.fromJson,
          toJson: (profile) => profile.toJson(),
        ),
      ),
      withInternetInterceptor: true,
    );
  }

  void updateFromUser(UserModel user) {
    updateData(
      data.copyWith(
        owner: data.owner.copyWith(fullName: user.name),
        accountDetails: data.accountDetails.updateFromUser(user),
      ),
    );
  }
}
