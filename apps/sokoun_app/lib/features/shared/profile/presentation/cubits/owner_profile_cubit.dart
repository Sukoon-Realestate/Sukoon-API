part of '../../imports.dart';

class OwnerProfileCubit extends AsyncCubit<OwnerProfileContent> {
  OwnerProfileCubit() : super(const OwnerProfileContent.initial());

  Future<void> getProfile() async {
    await executeAsyncWithBaseModel(
      operation: () => baseCrudUseCase.call(
        CrudBaseParmas<OwnerProfileContent>(
          api: ApiConstants.ownerProfile,
          httpRequestType: HttpRequestType.get,
          cacheKey: OwnerProfileContent.cacheKey,
          mapper: (json) => OwnerProfileContent.fromJson(_profileJsonMap(json)),
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
