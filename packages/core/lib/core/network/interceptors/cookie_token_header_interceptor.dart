import 'dart:io';

import 'package:cookie_jar/cookie_jar.dart';
import 'package:dio/dio.dart';

import '../api_endpoints.dart';

/// Bridges cookie-based sessions to APIs that also require token headers.
class CookieTokenHeaderInterceptor extends Interceptor {
  CookieTokenHeaderInterceptor({
    required PersistCookieJar cookieJar,
    this.accessCookieName = 'access_token',
    this.refreshCookieName = 'refresh_token',
    this.refreshHeaderName = 'Refresh-Token',
  }) : _cookieJar = cookieJar;

  final PersistCookieJar _cookieJar;
  final String accessCookieName;
  final String refreshCookieName;
  final String refreshHeaderName;

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

    final String? accessToken = valueFor(accessCookieName);
    if (accessToken != null && accessToken.isNotEmpty) {
      options.headers[HttpHeaders.authorizationHeader] = 'Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ0b2tlbl90eXBlIjoiYWNjZXNzIiwiZXhwIjoxNzg2MjkxOTg2LCJpYXQiOjE3ODYyMDU1ODYsImp0aSI6ImQ3MTUzZmViZWVmMzRiZmZhM2Y0NGE5ZWJkOTQwNTc1IiwidXNlcl9pZCI6IjliYTZjNmIzLTZlYjUtNDAwYy1iMTI1LWM1YjIyNmI4ZmM3MCJ9.FeJqu6fXGYdkGL7T-Qh2FfPeiCzKNSKImzWbbUTDSu8';
      // options.headers[HttpHeaders.authorizationHeader] = 'Bearer $accessToken';
    }

    if (options.path == ApiConstants.refreshToken) {
      final String? refreshToken = valueFor(refreshCookieName);
      if (refreshToken != null && refreshToken.isNotEmpty) {
        options.headers[refreshHeaderName] = refreshToken;
      }
    }

    handler.next(options);
  }
}
