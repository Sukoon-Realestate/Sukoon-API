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
    // if (accessToken.isNotNull && accessToken!.isNotEmpty) {
    //   options.headers[HttpHeaders.authorizationHeader] = 'Bearer $accessToken';
    // }

    options.headers[HttpHeaders.authorizationHeader] = 'Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ0b2tlbl90eXBlIjoiYWNjZXNzIiwiZXhwIjoxNzg4MTA0NDk2LCJpYXQiOjE3ODgwMTgwOTYsImp0aSI6ImU5MGE3MTU2MzMxODQ5MWY4MDFiMWJiMTM4Y2VmM2Q5IiwidXNlcl9pZCI6IjllZWY0MjAxLTBjYTQtNGZjMS1iOTFmLTllZjI3NTUxYzBlYSJ9.7pb3D2K3vY0WUNDrMUegy4mkSop6d-8hYNxQTOS0ku0';
    if (options.path == ApiConstants.refreshToken) {
      final String? refreshToken = valueFor(refreshCookieName);
      if (refreshToken != null && refreshToken.isNotEmpty) {
        options.headers[refreshHeaderName] = refreshToken;
      }
    }

    handler.next(options);
  }
}
