import 'package:melos_core/core/base_crud/code/presentation/cubit/base_cubit/async_cubit.dart';
import 'package:melos_core/core/shared/models/user_models/user_model.dart';
import 'package:melos_core/core/shared/user_cubit/user_cubit.dart';
import 'package:sokoun_app/features/shared/auth/data/auth_session_data.dart';

class LoginCubit extends AsyncCubit<UserModel> {
  LoginCubit() : super(UserModel.initial());

  Future<void> login({
    required String email,
    required String password,
    required void Function() onSuccess,
  }) async {
    UserModel? authenticatedUser;

    await executeAsyncWithBaseModel(
      showMsgOnSuccess: true,
      withInternetInterceptor: true,
      operation: () => AuthSessionData.loginWithCredentials(
        email: email,
        password: password,
      ),
      onSuccess: (response) => authenticatedUser = response.data,
    );

    final UserModel? user = authenticatedUser;
    if (user == null) {
      return;
    }

    await UserCubit.instance.setUserLoggedIn(user: user);
    onSuccess();
  }
}
