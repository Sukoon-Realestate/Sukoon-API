import 'dart:io';

import 'package:dio/dio.dart';

import '../api_endpoints.dart';
import 'session_cookie_manager.dart';

class UnauthorizedInterceptor extends Interceptor {
  UnauthorizedInterceptor({
    required Dio dio,
    required Future<bool> Function() canRefreshSession,
    required Future<void> Function(int generation) onSessionExpired,
  }) : _dio = dio,
       _canRefreshSession = canRefreshSession,
       _onSessionExpired = onSessionExpired;

  static const String _retryKey = 'retried_after_cookie_refresh';

  final Dio _dio;
  final Future<bool> Function() _canRefreshSession;
  final Future<void> Function(int generation) _onSessionExpired;
  Future<void>? _refreshFuture;
  int? _refreshGeneration;

  @override
  Future<void> onError(
    DioException err,
    ErrorInterceptorHandler handler,
  ) async {
    final RequestOptions request = err.requestOptions;
    if (!SessionCookieManager.isCurrent(request) ||
        err.response?.statusCode != HttpStatus.unauthorized ||
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

    if (!SessionCookieManager.isCurrent(request)) {
      handler.next(SessionCookieManager.staleRequest(request));
      return;
    }

    try {
      await _refreshSession(
        request.extra[SessionCookieManager.generationKey] as int,
      );
      if (!SessionCookieManager.isCurrent(request)) {
        handler.next(SessionCookieManager.staleRequest(request));
        return;
      }

      request
        ..headers.remove(HttpHeaders.cookieHeader)
        ..extra[_retryKey] = true;
      if (request.data is FormData) {
        request.data = (request.data as FormData).clone();
      }

      final Response<dynamic> response = await _dio.fetch<dynamic>(request);
      handler.resolve(response);
    } catch (error) {
      // A failed retry (403, offline, server error) is not an expired session.
      if (SessionCookieManager.isCurrent(request) &&
          error is DioException &&
          error.response?.statusCode == HttpStatus.unauthorized) {
        await _onSessionExpired(
          request.extra[SessionCookieManager.generationKey] as int,
        );
      }
      if (error is DioException) {
        handler.next(error);
        return;
      }
      handler.next(err);
    }
  }

  Future<void> _refreshSession(int generation) {
    final Future<void>? pendingRefresh = _refreshFuture;
    if (pendingRefresh != null && _refreshGeneration == generation) {
      return pendingRefresh;
    }

    final Future<void> refresh = _dio
        .post<void>(
          ApiConstants.refreshToken,
          options: Options(
            extra: {
              _retryKey: true,
              SessionCookieManager.generationKey: generation,
            },
          ),
        )
        .then((_) {});
    _refreshFuture = refresh;
    _refreshGeneration = generation;
    return refresh.whenComplete(() {
      if (identical(_refreshFuture, refresh)) {
        _refreshFuture = null;
      }
    });
  }
}
