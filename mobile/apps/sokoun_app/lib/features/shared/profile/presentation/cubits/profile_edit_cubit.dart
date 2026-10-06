part of '../../imports.dart';

class ProfileEditCubit extends AsyncCubit<Map<String, dynamic>> {
  ProfileEditCubit() : super(const {});

  Future<void> editProfile({
    required ProfileEditBody body,
    bool updateUser = false,
    required void Function() onSuccess,
  }) async {
    if (isClosed || isLoading) return;
    await executeAsyncWithBaseModel(
      showMsgOnSuccess: true,
      operation: () => baseCrudUseCase.call(
        CrudBaseParmas<Map<String, dynamic>>(
          api: updateUser
              ? ApiConstants.updateUserProfile
              : ApiConstants.editProfile,
          httpRequestType: HttpRequestType.patch,
          body: updateUser ? body.toUserJson() : body.toJson(),
          isFromData: true,
          mapper: (json) => json is Map
              ? Map<String, dynamic>.from(json)
              : <String, dynamic>{},
        ),
      ),
      onSuccess: (_) {
        ObjectBoxCacheService.remove('editable_user_profile');
        onSuccess();
      },
    );
  }
}
