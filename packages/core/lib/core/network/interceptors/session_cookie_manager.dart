import 'package:dio/dio.dart';
import 'package:dio_cookie_manager/dio_cookie_manager.dart';

import '../account_session.dart';

/// Serializes cookie writes and logout, rejecting work from older accounts.
class SessionCookieManager extends CookieManager {
  SessionCookieManager(super.cookieJar);

  static const generationKey = 'account_session_generation';
  Future<void> _pending = Future<void>.value();

  static bool isCurrent(RequestOptions request) =>
      request.extra[generationKey] == AccountSession.generation;

  static DioException staleRequest(RequestOptions request) => DioException(
    requestOptions: request,
    type: DioExceptionType.cancel,
    message: 'The account session changed.',
  );

  Future<T> _serialize<T>(Future<T> Function() operation) {
    final Future<T> result = _pending.then((_) => operation());
    _pending = result.then<void>((_) {}, onError: (Object _, StackTrace __) {});
    return result;
  }

  Future<void> clear({int? generation, bool expire = false}) => _serialize(
    () async {
      if (generation != null && generation != AccountSession.generation) return;
      if (expire) AccountSession.notifyExpired();
      await cookieJar.deleteAll();
    },
  );

  @override
  Future<String> loadCookies(RequestOptions options) => _serialize(() async {
    if (!isCurrent(options)) throw staleRequest(options);
    final String cookies = await super.loadCookies(options);
    if (!isCurrent(options)) throw staleRequest(options);
    return cookies;
  });

  @override
  Future<void> saveCookies(Response response) => _serialize(() async {
    if (!isCurrent(response.requestOptions)) {
      throw staleRequest(response.requestOptions);
    }
    await super.saveCookies(response);
  });
}
