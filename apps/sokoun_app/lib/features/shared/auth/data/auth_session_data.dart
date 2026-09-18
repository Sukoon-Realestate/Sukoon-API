import 'package:melos_core/config/res/config_imports.dart';
import 'package:melos_core/core/base_crud/code/domain/base_domain_imports.dart';
import 'package:melos_core/core/base_crud/code/domain/usecases/pagination_response.dart';
import 'package:melos_core/core/error/failure.dart';
import 'package:melos_core/core/network/api_endpoints.dart';
import 'package:melos_core/core/shared/models/user_models/user_model.dart';
import 'package:multiple_result/multiple_result.dart';
import 'package:sokoun_app/features/shared/auth/data/models/google_login.dart';

abstract interface class AuthSessionDataSource {
  Future<Result<BaseModel<UserModel>, Failure>> loginWithCredentials({
    required String email,
    required String password,
  });

  Future<Result<BaseModel<UserModel>, Failure>> loginWithGoogle({
    required GoogleLoginBody body,
  });
}

final class AuthSessionApiDataSource implements AuthSessionDataSource {
  const AuthSessionApiDataSource();

  static const String _currentUserCacheKey = 'auth_current_user';

  @override
  Future<Result<BaseModel<UserModel>, Failure>> loginWithCredentials({
    required String email,
    required String password,
  }) async {
    return _authenticateAndGetCurrentUser(
      api: ApiConstants.login,
      body: {'email': email, 'password': password},
    );
  }

  @override
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
    final BaseCrudUseCase baseCrudUseCase = injector<BaseCrudUseCase>();
    final Result<BaseModel<Object?>, Failure> authenticationResult =
        await baseCrudUseCase.call<Object?>(
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

    return baseCrudUseCase.call<UserModel>(
      CrudBaseParmas<UserModel>(
        api: ApiConstants.currentUser,
        httpRequestType: HttpRequestType.get,
        cacheKey: _currentUserCacheKey,
        mapper: _mapCurrentUser,
        fromCacheJson: _mapCurrentUser,
        toJson: _serializeCurrentUser,
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

  static Map<String, dynamic> _serializeCurrentUser(UserModel user) => {
    ...user.toJson(),
    'full_name': user.name,
  };
}

abstract final class AuthSessionData {
  static AuthSessionDataSource get source =>
      injector.isRegistered<AuthSessionDataSource>()
      ? injector<AuthSessionDataSource>()
      : const AuthSessionApiDataSource();

  static Future<Result<BaseModel<UserModel>, Failure>> loginWithCredentials({
    required String email,
    required String password,
  }) => source.loginWithCredentials(email: email, password: password);

  static Future<Result<BaseModel<UserModel>, Failure>> loginWithGoogle({
    required GoogleLoginBody body,
  }) => source.loginWithGoogle(body: body);
}
