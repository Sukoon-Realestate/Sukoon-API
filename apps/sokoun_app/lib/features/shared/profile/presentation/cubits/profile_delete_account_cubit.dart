part of '../../imports.dart';

class ProfileDeleteAccountCubit extends AsyncCubit<Map<String, dynamic>> {
  ProfileDeleteAccountCubit() : super(const {});

  Future<void> deleteAccount({required void Function() onSuccess}) async {
    await executeAsyncWithBaseModel(
      operation: () => baseCrudUseCase.call(
        CrudBaseParmas<Map<String, dynamic>>(
          api: ApiConstants.deleteAccount,
          httpRequestType: HttpRequestType.delete,
          mapper: (json) => json is Map
              ? Map<String, dynamic>.from(json)
              : <String, dynamic>{},
        ),
      ),
      onSuccess: (_) => onSuccess(),
    );
  }
}
