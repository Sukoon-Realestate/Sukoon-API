import 'dart:async';
import 'dart:convert';
import 'dart:io';

import 'package:flutter_test/flutter_test.dart';
import 'package:melos_core/core/network/dio_service.dart';
import 'package:melos_core/core/network/account_session.dart';
import 'package:melos_core/core/network/network_request.dart';

void main() {
  setUp(AccountSession.end);
  tearDown(AccountSession.end);

  for (final retryStatus in [
    HttpStatus.forbidden,
    HttpStatus.internalServerError,
  ]) {
    test(
      'a refreshed request failing with $retryStatus does not sign out',
      () async {
        final directory = await Directory.systemTemp.createTemp(
          'sokoun_refresh_error_',
        );
        final server = await HttpServer.bind(InternetAddress.loopbackIPv4, 0);
        int protectedRequests = 0;
        addTearDown(() async {
          await server.close(force: true);
          await directory.delete(recursive: true);
        });
        server.listen((request) async {
          request.response.headers.contentType = ContentType.json;
          if (request.uri.path == '/auth/login/') {
            request.response.cookies
              ..add(Cookie('access_token', 'old')..path = '/')
              ..add(Cookie('refresh_token', 'refresh')..path = '/');
          } else if (request.uri.path == '/auth/jwt/refresh/') {
            request.response.cookies.add(
              Cookie('access_token', 'fresh')..path = '/',
            );
          } else {
            protectedRequests++;
            request.response.statusCode = protectedRequests == 1
                ? HttpStatus.unauthorized
                : retryStatus;
          }
          request.response.write(jsonEncode({'data': true}));
          await request.response.close();
        });
        final service = DioService(
          initialBaseUrl: 'http://${server.address.host}:${server.port}/',
          initialLanguageCode: 'en',
          cookieDirectoryProvider: () async => directory,
        );
        await service.callApi(
          NetworkRequest(path: 'auth/login/', method: RequestMethod.post),
        );
        AccountSession.begin('account-a');
        await expectLater(
          service.callApi(
            NetworkRequest(path: 'protected/', method: RequestMethod.get),
          ),
          throwsA(anything),
        );
        expect(protectedRequests, 2);
        expect(AccountSession.userId, 'account-a');
        expect(await service.getAccessToken(), 'fresh');
      },
    );
  }

  for (final int lateStatus in [HttpStatus.ok, HttpStatus.unauthorized]) {
    test(
      'late $lateStatus cannot overwrite or retry with another account cookies',
      () async {
        final directory = await Directory.systemTemp.createTemp(
          'sokoun_isolation_',
        );
        final server = await HttpServer.bind(InternetAddress.loopbackIPv4, 0);
        final received = Completer<void>();
        final release = Completer<void>();
        int mutations = 0;
        int refreshes = 0;
        addTearDown(() async {
          await server.close(force: true);
          await directory.delete(recursive: true);
        });
        server.listen((request) async {
          request.response.headers.contentType = ContentType.json;
          if (request.uri.path == '/auth/login/') {
            final String account = request.uri.queryParameters['account']!;
            request.response.cookies
              ..add(Cookie('access_token', account)..path = '/')
              ..add(Cookie('refresh_token', account)..path = '/');
          } else if (request.uri.path == '/mutation/') {
            mutations++;
            if (!received.isCompleted) received.complete();
            await release.future;
            request.response.statusCode = lateStatus;
            request.response.cookies.add(
              Cookie('access_token', 'stale-account')..path = '/',
            );
          } else if (request.uri.path == '/auth/jwt/refresh/') {
            refreshes++;
          }
          request.response.write(
            jsonEncode({
              'data': request.cookies
                  .map((cookie) => '${cookie.name}=${cookie.value}')
                  .join(';'),
            }),
          );
          await request.response.close();
        });
        final service = DioService(
          initialBaseUrl: 'http://${server.address.host}:${server.port}/',
          initialLanguageCode: 'en',
          cookieDirectoryProvider: () async => directory,
        );
        Future<void> login(String id) async {
          await service.callApi(
            NetworkRequest(
              path: 'auth/login/',
              method: RequestMethod.post,
              queryParameters: {'account': id},
            ),
          );
          AccountSession.begin(id);
        }

        await login('account-a');
        final pending = service.callApi(
          NetworkRequest(
            path: 'mutation/',
            method: RequestMethod.post,
            body: const {'value': 1},
          ),
        );
        final rejected = expectLater(pending, throwsA(anything));
        await received.future;
        AccountSession.end();
        await service.clearSessionCookies();
        await login('account-b');
        release.complete();
        await rejected;
        final cookies = await service.callApi<String>(
          NetworkRequest(path: 'echo/', method: RequestMethod.get),
          mapper: (json) => json as String,
        );
        expect(cookies.data, contains('access_token=account-b'));
        expect(cookies.data, isNot(contains('stale-account')));
        expect(AccountSession.userId, 'account-b');
        expect(mutations, 1);
        expect(refreshes, 0);
      },
    );
  }

  for (final int refreshStatus in [HttpStatus.ok, HttpStatus.unauthorized]) {
    test(
      'an in-flight refresh $refreshStatus cannot replace or expire a new session',
      () async {
        final directory = await Directory.systemTemp.createTemp(
          'sokoun_refresh_isolation_',
        );
        final server = await HttpServer.bind(InternetAddress.loopbackIPv4, 0);
        final refreshing = Completer<void>();
        final release = Completer<void>();
        int mutations = 0;
        addTearDown(() async {
          await server.close(force: true);
          await directory.delete(recursive: true);
        });
        server.listen((request) async {
          request.response.headers.contentType = ContentType.json;
          if (request.uri.path == '/login/') {
            final account = request.uri.queryParameters['account']!;
            request.response.cookies
              ..add(Cookie('access_token', account)..path = '/')
              ..add(Cookie('refresh_token', account)..path = '/');
          } else if (request.uri.path == '/mutation/') {
            mutations++;
            request.response.statusCode = HttpStatus.unauthorized;
          } else if (request.uri.path == '/auth/jwt/refresh/') {
            refreshing.complete();
            await release.future;
            request.response.statusCode = refreshStatus;
            request.response.cookies.add(
              Cookie('access_token', 'refreshed-old-account')..path = '/',
            );
          }
          request.response.write(jsonEncode({'data': true}));
          await request.response.close();
        });
        final service = DioService(
          initialBaseUrl: 'http://${server.address.host}:${server.port}/',
          initialLanguageCode: 'en',
          cookieDirectoryProvider: () async => directory,
        );
        Future<void> login(String id) async {
          await service.callApi(
            NetworkRequest(
              path: 'login/',
              method: RequestMethod.post,
              queryParameters: {'account': id},
            ),
          );
          AccountSession.begin(id);
        }

        await login('a');
        final rejected = expectLater(
          service.callApi(
            NetworkRequest(path: 'mutation/', method: RequestMethod.post),
          ),
          throwsA(anything),
        );
        await refreshing.future;
        AccountSession.end();
        await service.clearSessionCookies();
        await login('b');
        release.complete();
        await rejected;
        expect(AccountSession.userId, 'b');
        expect(await service.getAccessToken(), 'b');
        expect(mutations, 1);
      },
    );
  }

  test(
    'a request waiting for initialization never dispatches in a later session',
    () async {
      final directory = await Directory.systemTemp.createTemp(
        'sokoun_queued_session_',
      );
      final server = await HttpServer.bind(InternetAddress.loopbackIPv4, 0);
      int requests = 0;
      server.listen((request) async {
        requests++;
        await request.response.close();
      });
      addTearDown(() async {
        await server.close(force: true);
        await directory.delete(recursive: true);
      });
      final ready = Completer<Directory>();
      final service = DioService(
        initialBaseUrl: 'http://${server.address.host}:${server.port}/',
        initialLanguageCode: 'en',
        cookieDirectoryProvider: () => ready.future,
      );
      AccountSession.begin('a');
      final rejected = expectLater(
        service.callApi(
          NetworkRequest(path: 'mutation/', method: RequestMethod.post),
        ),
        throwsA(anything),
      );
      AccountSession.begin('b');
      ready.complete(directory);
      await rejected;
      expect(requests, 0);
      expect(AccountSession.userId, 'b');
    },
  );

  test(
    'a rejected signed-in session expires even with no refresh cookie',
    () async {
      final Directory cookieDirectory = await Directory.systemTemp.createTemp(
        'sokoun_cookie_expiry_test_',
      );
      final HttpServer server = await HttpServer.bind(
        InternetAddress.loopbackIPv4,
        0,
      );
      addTearDown(() async {
        await server.close(force: true);
        await cookieDirectory.delete(recursive: true);
      });
      server.listen((request) async {
        request.response
          ..statusCode = HttpStatus.unauthorized
          ..headers.contentType = ContentType.json
          ..write(jsonEncode({'message': 'Session expired'}));
        await request.response.close();
      });
      final DioService service = DioService(
        initialBaseUrl: 'http://${server.address.host}:${server.port}/',
        initialLanguageCode: 'en',
        cookieDirectoryProvider: () async => cookieDirectory,
      );
      AccountSession.begin('expired-account');
      final Future<void> expired = AccountSession.expired.first;
      await expectLater(
        service.callApi<bool>(
          NetworkRequest(method: RequestMethod.get, path: 'protected/'),
        ),
        throwsA(anything),
      );
      await expired.timeout(const Duration(seconds: 2));
      expect(AccountSession.userId, isNull);
      expect(await service.hasSessionCookies(), isFalse);
    },
  );

  test(
    'persists backend cookies, restores them, and clears the session',
    () async {
      final Directory cookieDirectory = await Directory.systemTemp.createTemp(
        'sokoun_cookie_test_',
      );
      final HttpServer server = await HttpServer.bind(
        InternetAddress.loopbackIPv4,
        0,
      );
      addTearDown(() async {
        await server.close(force: true);
        if (await cookieDirectory.exists()) {
          await cookieDirectory.delete(recursive: true);
        }
      });

      server.listen((HttpRequest request) async {
        final bool hasAccessCookie = request.cookies.any(
          (cookie) =>
              cookie.name == 'access_token' && cookie.value == 'server-token',
        );
        if (request.uri.path == '/auth/login/') {
          request.response.cookies.add(
            Cookie('access_token', 'server-token')
              ..httpOnly = true
              ..path = '/',
          );
        }

        request.response.headers.contentType = ContentType.json;
        request.response.write(
          jsonEncode({
            'key': '',
            'message': '',
            'data': request.uri.path == '/auth/login/' || hasAccessCookie,
          }),
        );
        await request.response.close();
      });

      final String baseUrl = 'http://${server.address.host}:${server.port}/';
      Future<Directory> cookieDirectoryProvider() async => cookieDirectory;

      final DioService loginService = DioService(
        initialBaseUrl: baseUrl,
        initialLanguageCode: 'en',
        cookieDirectoryProvider: cookieDirectoryProvider,
      );
      await loginService.callApi<bool>(
        NetworkRequest(
          method: RequestMethod.post,
          path: 'auth/login/',
          body: const {'email': 'user@example.com', 'password': 'password'},
        ),
        mapper: (json) => json as bool,
      );

      final DioService restoredService = DioService(
        initialBaseUrl: baseUrl,
        initialLanguageCode: 'en',
        cookieDirectoryProvider: cookieDirectoryProvider,
      );
      expect(await restoredService.hasSessionCookies(), isTrue);

      final protectedResponse = await restoredService.callApi<bool>(
        NetworkRequest(method: RequestMethod.get, path: 'protected/'),
        mapper: (json) => json as bool,
      );
      expect(protectedResponse.data, isTrue);

      await restoredService.clearSessionCookies();
      expect(await restoredService.hasSessionCookies(), isFalse);

      final clearedResponse = await restoredService.callApi<bool>(
        NetworkRequest(method: RequestMethod.get, path: 'protected/'),
        mapper: (json) => json as bool,
      );
      expect(clearedResponse.data, isFalse);
    },
  );

  test(
    'refreshes cookie authentication once and retries the request',
    () async {
      final Directory cookieDirectory = await Directory.systemTemp.createTemp(
        'sokoun_cookie_refresh_test_',
      );
      final HttpServer server = await HttpServer.bind(
        InternetAddress.loopbackIPv4,
        0,
      );
      int refreshCount = 0;
      addTearDown(() async {
        await server.close(force: true);
        if (await cookieDirectory.exists()) {
          await cookieDirectory.delete(recursive: true);
        }
      });

      server.listen((HttpRequest request) async {
        String? cookieValue(String name) {
          for (final Cookie cookie in request.cookies) {
            if (cookie.name == name) {
              return cookie.value;
            }
          }
          return null;
        }

        final String? accessToken = cookieValue('access_token');
        final String? refreshToken = cookieValue('refresh_token');
        final String? authorization = request.headers.value(
          HttpHeaders.authorizationHeader,
        );
        if (request.uri.path == '/auth/login/') {
          request.response.cookies
            ..add(
              Cookie('access_token', 'expired-token')
                ..httpOnly = true
                ..path = '/',
            )
            ..add(
              Cookie('refresh_token', 'server-refresh-token')
                ..httpOnly = true
                ..path = '/auth/jwt/refresh/',
            );
        } else if (request.uri.path == '/auth/jwt/refresh/' &&
            refreshToken == 'server-refresh-token' &&
            authorization == 'Bearer server-refresh-token') {
          refreshCount++;
          request.response.cookies.add(
            Cookie('access_token', 'fresh-token')
              ..httpOnly = true
              ..path = '/',
          );
        } else if (request.uri.path == '/protected/' &&
            (accessToken != 'fresh-token' ||
                authorization != 'Bearer fresh-token')) {
          request.response.statusCode = HttpStatus.unauthorized;
        }

        request.response.headers.contentType = ContentType.json;
        request.response.write(
          jsonEncode({
            'key': '',
            'message': '',
            'data':
                request.uri.path != '/protected/' ||
                accessToken == 'fresh-token',
          }),
        );
        await request.response.close();
      });

      final String baseUrl = 'http://${server.address.host}:${server.port}/';
      final DioService service = DioService(
        initialBaseUrl: baseUrl,
        initialLanguageCode: 'en',
        cookieDirectoryProvider: () async => cookieDirectory,
      );

      await expectLater(
        service.callApi<bool>(
          NetworkRequest(method: RequestMethod.get, path: 'protected/'),
          mapper: (json) => json as bool,
        ),
        throwsA(anything),
      );
      expect(refreshCount, 0);

      await service.callApi<bool>(
        NetworkRequest(
          method: RequestMethod.post,
          path: 'auth/login/',
          body: const {'email': 'user@example.com', 'password': 'password'},
        ),
        mapper: (json) => json as bool,
      );

      final protectedResponse = await service.callApi<bool>(
        NetworkRequest(method: RequestMethod.get, path: 'protected/'),
        mapper: (json) => json as bool,
      );

      expect(refreshCount, 1);
      expect(protectedResponse.data, isTrue);
    },
  );
}
