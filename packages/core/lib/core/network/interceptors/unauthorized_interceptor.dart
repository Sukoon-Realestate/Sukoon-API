import 'dart:io';

import 'package:dio/dio.dart';

import '../api_endpoints.dart';
import '../session_refresh_coordinator.dart';
import 'session_cookie_manager.dart';

class UnauthorizedInterceptor extends Interceptor {
  UnauthorizedInterceptor({
    required Dio dio,
    required SessionRefreshCoordinator refreshCoordinator,
    required Future<bool> Function() canRefreshSession,
    required Future<void> Function(int generation) onSessionExpired,
  }) : _dio = dio,
       _refreshCoordinator = refreshCoordinator,
       _canRefreshSession = canRefreshSession,
       _onSessionExpired = onSessionExpired;

  static const String _retryKey = 'retried_after_cookie_refresh';

  final Dio _dio;
  final Future<bool> Function() _canRefreshSession;
  final Future<void> Function(int generation) _onSessionExpired;
  final SessionRefreshCoordinator _refreshCoordinator;

  @override
  Future<void> onError(
    DioException err,
    ErrorInterceptorHandler handler,
  ) async {
    final RequestOptions request = err.requestOptions;
    if (request.cancelToken?.isCancelled ?? false) {
      handler.next(request.cancelToken!.cancelError!);
      return;
    }
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
      if (request.cancelToken?.isCancelled ?? false) {
        throw request.cancelToken!.cancelError!;
      }
      await _refreshCoordinator.refresh(
        request.extra[SessionCookieManager.generationKey] as int,
        requestRevision:
            request.extra[SessionRefreshCoordinator.revisionKey] as int?,
      );
      if (request.cancelToken?.isCancelled ?? false) {
        throw request.cancelToken!.cancelError!;
      }
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
}
