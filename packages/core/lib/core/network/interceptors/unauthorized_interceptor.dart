import 'dart:io';

import 'package:dio/dio.dart';

import '../../helpers/cache_service.dart';
import '../api_endpoints.dart';

class UnauthorizedInterceptor extends Interceptor {
  UnauthorizedInterceptor(this._dio);

  static const String _retryKey = 'retried_after_token_refresh';
  static const String _tokenKey = 'token';

  final Dio _dio;

  @override
  Future<void> onError(
    DioException err,
    ErrorInterceptorHandler handler,
  ) async {
    final RequestOptions request = err.requestOptions;
    if (err.response?.statusCode != HttpStatus.unauthorized ||
        request.extra[_retryKey] == true ||
        request.headers[HttpHeaders.authorizationHeader] == null) {
      handler.next(err);
      return;
    }

    try {
      final Response<dynamic> refreshResponse = await _dio.post<dynamic>(
        ApiConstants.refreshToken,
        options: Options(
          headers: {
            HttpHeaders.authorizationHeader:
                request.headers[HttpHeaders.authorizationHeader],
          },
          extra: {_retryKey: true},
        ),
      );
      final String token = refreshResponse.data['data']['token'];

      await SecureStorage.write(_tokenKey, token);
      _dio.options.headers[HttpHeaders.authorizationHeader] = 'Bearer $token';

      request
        ..headers[HttpHeaders.authorizationHeader] = 'Bearer $token'
        ..extra[_retryKey] = true;
      if (request.data is FormData) {
        request.data = (request.data as FormData).clone();
      }

      final Response<dynamic> response = await _dio.fetch<dynamic>(request);
      handler.resolve(response);
    } catch (_) {
      handler.next(err);
    }
  }
}
