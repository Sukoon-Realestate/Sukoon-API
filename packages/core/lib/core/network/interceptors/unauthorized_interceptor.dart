import 'dart:io';

import 'package:dio/dio.dart';

import '../api_endpoints.dart';

class UnauthorizedInterceptor extends Interceptor {
  UnauthorizedInterceptor({
    required Dio dio,
    required Future<bool> Function() canRefreshSession,
    required Future<void> Function() onSessionExpired,
  }) : _dio = dio,
       _canRefreshSession = canRefreshSession,
       _onSessionExpired = onSessionExpired;

  static const String _retryKey = 'retried_after_cookie_refresh';

  final Dio _dio;
  final Future<bool> Function() _canRefreshSession;
  final Future<void> Function() _onSessionExpired;
  Future<void>? _refreshFuture;

  @override
  Future<void> onError(
    DioException err,
    ErrorInterceptorHandler handler,
  ) async {
    final RequestOptions request = err.requestOptions;
    if (err.response?.statusCode != HttpStatus.unauthorized ||
        request.extra[_retryKey] == true ||
        request.path == ApiConstants.refreshToken) {
      handler.next(err);
      return;
    }

    try {
      if (!await _canRefreshSession()) {
        handler.next(err);
        return;
      }
    } catch (_) {
      handler.next(err);
      return;
    }

    try {
      await _refreshSession();

      request
        ..headers.remove(HttpHeaders.cookieHeader)
        ..extra[_retryKey] = true;
      if (request.data is FormData) {
        request.data = (request.data as FormData).clone();
      }

      final Response<dynamic> response = await _dio.fetch<dynamic>(request);
      handler.resolve(response);
    } catch (_) {
      await _onSessionExpired();
      handler.next(err);
    }
  }

  Future<void> _refreshSession() {
    final Future<void>? pendingRefresh = _refreshFuture;
    if (pendingRefresh != null) {
      return pendingRefresh;
    }

    final Future<void> refresh = _dio
        .post<void>(
          ApiConstants.refreshToken,
          options: Options(extra: {_retryKey: true}),
        )
        .then((_) {});
    _refreshFuture = refresh;
    return refresh.whenComplete(() {
      if (identical(_refreshFuture, refresh)) {
        _refreshFuture = null;
      }
    });
  }
}
