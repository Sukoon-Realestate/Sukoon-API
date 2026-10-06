import 'dart:io';

/// Reads backend cookie names and cookies persisted by older app versions.
abstract final class SessionTokenCookies {
  static const String accessCookieName = 'access';
  static const String refreshCookieName = 'refresh';

  static String? accessToken(
    Iterable<Cookie> cookies, {
    String cookieName = accessCookieName,
  }) => _valueFor(cookies, [cookieName, accessCookieName, 'access_token']);

  static String? refreshToken(
    Iterable<Cookie> cookies, {
    String cookieName = refreshCookieName,
  }) => _valueFor(cookies, [cookieName, refreshCookieName, 'refresh_token']);

  static String? _valueFor(Iterable<Cookie> cookies, List<String> names) {
    for (final String name in names) {
      for (final Cookie cookie in cookies) {
        if (cookie.name == name && cookie.value.isNotEmpty) return cookie.value;
      }
    }
    return null;
  }
}
