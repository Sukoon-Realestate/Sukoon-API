part of '../../imports.dart';

class ChangePasswordCubit extends AsyncCubit<bool> {
  ChangePasswordCubit() : super(false);
  Future<bool> save(ChangePasswordBody body) async {
    if (isClosed || isLoading) return false;
    bool saved = false;
    await executeAsyncWithBaseModel(
      showMsgOnSuccess: true,
      operation: () => baseCrudUseCase.call(
        CrudBaseParmas<bool>(
          api: ApiConstants.changePassword,
          httpRequestType: HttpRequestType.post,
          body: body.toJson(),
          mapper: (_) => true,
        ),
      ),
      onSuccess: (_) => saved = true,
    );
    return !isClosed && saved;
  }
}
