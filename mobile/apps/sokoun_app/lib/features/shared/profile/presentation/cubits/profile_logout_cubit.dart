part of '../../imports.dart';

class ProfileLogoutCubit extends AsyncCubit<bool> {
  ProfileLogoutCubit() : super(false);
  Future<bool> logout() async {
    if (isClosed || isLoading) return false;
    bool succeeded = false;
    await executeAsyncWithBaseModel(
      operation: () => baseCrudUseCase.call(
        CrudBaseParmas<bool>(
          api: ApiConstants.logout,
          httpRequestType: HttpRequestType.post,
          mapper: (_) => true,
        ),
      ),
      onSuccess: (_) => succeeded = true,
    );
    return succeeded;
  }
}
