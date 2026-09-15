import 'package:melos_core/core/base_crud/code/domain/base_domain_imports.dart';
import 'package:melos_core/core/base_crud/code/presentation/cubit/base_cubit/async_cubit.dart';
import 'package:melos_core/core/network/api_endpoints.dart';
import 'package:melos_core/core/shared/models/user_models/user_model.dart';
import 'package:melos_core/core/shared/user_cubit/user_cubit.dart';
import 'package:sokoun_app/features/shared/auth/data/models/google_login.dart';

class GoogleLoginCubit extends AsyncCubit<UserModel> {
  GoogleLoginCubit() : super(UserModel.initial());

  Future<void> login({
    required GoogleLoginBody body,
    required void Function() onSuccess,
  }) async {
    UserModel? authenticatedUser;

    await executeAsyncWithBaseModel(
      showMsgOnSuccess: true,
      operation: () => baseCrudUseCase.call(
        CrudBaseParmas<UserModel>(
          api: ApiConstants.googleLogin,
          httpRequestType: HttpRequestType.post,
          body: body.toJson(),
          mapper: _mapUser,
        ),
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

  static UserModel _mapUser(dynamic json) {
    if (json is! Map) {
      throw const FormatException('Invalid Google login response data');
    }

    final Map<String, dynamic> data = Map<String, dynamic>.from(json);
    final Object? nestedUser = data['user'];
    final Map<String, dynamic> userJson = nestedUser is Map
        ? Map<String, dynamic>.from(nestedUser)
        : data;
    return UserModel.fromJson(userJson);
  }
}
