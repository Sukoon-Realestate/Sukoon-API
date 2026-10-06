import 'dart:io';

import 'package:cookie_jar/cookie_jar.dart';
import 'package:dio/dio.dart';

import '../api_endpoints.dart';
import '../session_token_cookies.dart';
import 'session_cookie_manager.dart';

class CookieTokenHeaderInterceptor extends Interceptor {
  CookieTokenHeaderInterceptor({
    required PersistCookieJar cookieJar,
    this.accessCookieName = SessionTokenCookies.accessCookieName,
    this.refreshCookieName = SessionTokenCookies.refreshCookieName,
  }) : _cookieJar = cookieJar;

  final PersistCookieJar _cookieJar;
  final String accessCookieName;
  final String refreshCookieName;

  @override
  Future<void> onRequest(
    RequestOptions options,
    RequestInterceptorHandler handler,
  ) async {
    if (!SessionCookieManager.isCurrent(options)) {
      handler.reject(SessionCookieManager.staleRequest(options));
      return;
    }
    final List<Cookie> cookies = await _cookieJar.loadForRequest(options.uri);
    if (!SessionCookieManager.isCurrent(options)) {
      handler.reject(SessionCookieManager.staleRequest(options));
      return;
    }

    final bool isRefresh = options.uri.path.endsWith(
      '/${ApiConstants.refreshToken}',
    );
    final String? token = isRefresh
        ? SessionTokenCookies.refreshToken(
            cookies,
            cookieName: refreshCookieName,
          )
        : SessionTokenCookies.accessToken(
            cookies,
            cookieName: accessCookieName,
          );

    if (token != null) {
      options.headers[HttpHeaders.authorizationHeader] = 'Bearer $token';
    } else {
      options.headers.remove(HttpHeaders.authorizationHeader);
    }

    handler.next(options);
  }
}
