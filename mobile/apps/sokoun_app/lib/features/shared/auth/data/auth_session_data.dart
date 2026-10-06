import 'package:melos_core/config/res/config_imports.dart';
import 'package:melos_core/core/base_crud/code/domain/base_domain_imports.dart';
import 'package:melos_core/core/base_crud/code/domain/usecases/pagination_response.dart';
import 'package:melos_core/core/error/failure.dart';
import 'package:melos_core/core/network/api_endpoints.dart';
import 'package:melos_core/core/shared/models/user_models/user_model.dart';
import 'package:melos_core/core/network/network_service.dart';
import 'package:melos_core/core/helpers/validators.dart';
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

  @override
  Future<Result<BaseModel<UserModel>, Failure>> loginWithCredentials({
    required String email,
    required String password,
  }) async {
    return _authenticateAndGetCurrentUser(
      api: ApiConstants.login,
      body: {'email': Validators.normalizeEmail(email), 'password': password},
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

    final result = await baseCrudUseCase.call<UserModel>(
      CrudBaseParmas<UserModel>(
        api: ApiConstants.currentUser,
        httpRequestType: HttpRequestType.get,
        mapper: _mapCurrentUser,
      ),
    );
    if (result.tryGetError() != null &&
        injector.isRegistered<NetworkService>()) {
      await injector<NetworkService>().clearSessionCookies();
    }
    return result;
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
    final UserModel user = UserModel.fromJson(userJson);
    if (user.id.isEmpty || user.id == '0') {
      throw const FormatException('Missing authenticated account ID');
    }
    return user;
  }
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
