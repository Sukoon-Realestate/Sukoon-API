import 'package:melos_core/core/base_crud/code/domain/base_domain_imports.dart';
import 'package:melos_core/core/base_crud/code/domain/usecases/pagination_response.dart';
import 'package:melos_core/core/error/failure.dart';
import 'package:melos_core/core/network/api_endpoints.dart';
import 'package:melos_core/core/shared/models/user_models/user_model.dart';
import 'package:multiple_result/multiple_result.dart';
import 'package:sokoun_app/features/shared/auth/data/models/google_login.dart';

class AuthSessionData {
  const AuthSessionData({required BaseCrudUseCase baseCrudUseCase})
    : _baseCrudUseCase = baseCrudUseCase;

  final BaseCrudUseCase _baseCrudUseCase;

  Future<Result<BaseModel<UserModel>, Failure>> loginWithCredentials({
    required String email,
    required String password,
  }) async {
    return _authenticateAndGetCurrentUser(
      api: ApiConstants.login,
      body: {'email': email, 'password': password},
    );
  }

  Future<Result<BaseModel<UserModel>, Failure>> loginWithGoogle({
    required GoogleLoginBody body,
  }) async {
    return _authenticateAndGetCurrentUser(
      api: ApiConstants.googleLogin,
      body: body.toJson(),
    );
  }

  Future<Result<BaseModel<UserModel>, Failure>> _authenticateAndGetCurrentUser({
    required String api,
    required Map<String, dynamic> body,
  }) async {
    final Result<BaseModel<Object?>, Failure> authenticationResult =
        await _baseCrudUseCase.call<Object?>(
          CrudBaseParmas<Object?>(
            api: api,
            httpRequestType: HttpRequestType.post,
            body: body,
          ),
        );
    final Failure? authenticationFailure = authenticationResult.tryGetError();
    if (authenticationFailure != null) {
      return Result.error(authenticationFailure);
    }

    return _baseCrudUseCase.call<UserModel>(
      CrudBaseParmas<UserModel>(
        api: ApiConstants.currentUser,
        httpRequestType: HttpRequestType.get,
        mapper: _mapCurrentUser,
      ),
    );
  }

  static UserModel _mapCurrentUser(dynamic json) {
    if (json is! Map) {
      throw const FormatException('Invalid current user response data');
    }

    final Map<String, dynamic> data = Map<String, dynamic>.from(json);
    final Object? nestedUser = data['user'];
    final Map<String, dynamic> userJson = nestedUser is Map
        ? Map<String, dynamic>.from(nestedUser)
        : data;
    return UserModel.fromJson(userJson);
  }
}
