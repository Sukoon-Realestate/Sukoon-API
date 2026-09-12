part of '../../imports.dart';

class ProfileEditCubit extends AsyncCubit<Map<String, dynamic>> {
  ProfileEditCubit() : super(const {});

  Future<void> editProfile({
    required ProfileEditBody body,
    required void Function() onSuccess,
  }) async {
    await executeAsyncWithBaseModel(
      operation: () => baseCrudUseCase.call(
        CrudBaseParmas<Map<String, dynamic>>(
          api: ApiConstants.editProfile,
          httpRequestType: HttpRequestType.patch,
          body: body.toJson(),
          isFromData: true,
          mapper: (json) => json is Map
              ? Map<String, dynamic>.from(json)
              : <String, dynamic>{},
        ),
      ),
      onSuccess: (_) => onSuccess(),
    );
  }
}
