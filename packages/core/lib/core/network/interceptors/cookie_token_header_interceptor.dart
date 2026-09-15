import 'dart:io';

import 'package:cookie_jar/cookie_jar.dart';
import 'package:dio/dio.dart';
import 'package:melos_core/core/extensions/object.dart';

import '../api_endpoints.dart';

/// Bridges cookie-based sessions to APIs that also require token headers.
class CookieTokenHeaderInterceptor extends Interceptor {
  CookieTokenHeaderInterceptor({
    required PersistCookieJar cookieJar,
    this.accessCookieName = 'access_token',
    this.refreshCookieName = 'refresh_token',
  }) : _cookieJar = cookieJar;

  final PersistCookieJar _cookieJar;
  final String accessCookieName;
  final String refreshCookieName;

  @override
  Future<void> onRequest(
    RequestOptions options,
    RequestInterceptorHandler handler,
  ) async {
    final List<Cookie> cookies = await _cookieJar.loadForRequest(options.uri);

    String? valueFor(String name) {
      for (final Cookie cookie in cookies) {
        if (cookie.name == name) {
          return cookie.value;
        }
      }
      return null;
    }

    final String tokenCookieName = options.path == ApiConstants.refreshToken
        ? refreshCookieName
        : accessCookieName;
    final String? token = valueFor(tokenCookieName);

    if (token.isNotNull && token!.isNotEmpty) {
      options.headers[HttpHeaders.authorizationHeader] = 'Bearer $token';
    } else {
      options.headers.remove(HttpHeaders.authorizationHeader);
    }

    handler.next(options);
  }
}
