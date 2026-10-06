import 'dart:async';
import 'dart:convert';
import 'dart:io';
import 'dart:typed_data';

import 'package:dio/dio.dart';
import 'package:dio/io.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:melos_core/core/error/exceptions.dart';
import 'package:melos_core/core/network/account_session.dart';
import 'package:melos_core/core/network/api_endpoints.dart';
import 'package:melos_core/core/network/dio_service.dart';
import 'package:melos_core/core/network/network_request.dart';
import 'package:melos_core/core/socket_service/web_socket_client.dart';

void main() {
  setUp(AccountSession.end);
  tearDown(AccountSession.end);

  for (final bool expiredCookie in [false, true]) {
    test(
      'backend cookies refresh expired access, cookie expired: $expiredCookie',
      () async {
        int protectedRequests = 0;
        int refreshes = 0;
        int expirations = 0;
        final subscription = AccountSession.expired.listen(
          (_) => expirations++,
        );
        addTearDown(subscription.cancel);
        final fixture = await _service(
          (request) async {
            if (request.uri.path == '/api/v1/auth/refresh/') {
              refreshes++;
              expect(request.method, 'POST');
              expect(await utf8.decoder.bind(request).join(), isEmpty);
              final String expectedRefresh = refreshes == 1
                  ? 'refresh'
                  : 'rotated';
              expect(
                request.headers.value(HttpHeaders.authorizationHeader),
                'Bearer $expectedRefresh',
              );
              expect(
                request.cookies.any(
                  (cookie) =>
                      cookie.name == 'refresh' &&
                      cookie.value == expectedRefresh,
                ),
                isTrue,
              );
              request.response.cookies
                ..add(Cookie('access', 'fresh')..path = '/')
                ..add(
                  Cookie('refresh', 'rotated')..path = '/api/v1/auth/refresh/',
                );
              return _respond(request);
            }
            protectedRequests++;
            final String? authorization = request.headers.value(
              HttpHeaders.authorizationHeader,
            );
            expect(
              authorization,
              protectedRequests == 1
                  ? (expiredCookie ? null : 'Bearer old')
                  : 'Bearer fresh',
            );
            await _respond(request, status: protectedRequests == 1 ? 401 : 200);
          },
          loginCookies: () => [
            Cookie('access', 'old')
              ..path = '/'
              ..maxAge = expiredCookie ? 0 : 3600,
            Cookie('refresh', 'refresh')..path = '/api/v1/auth/refresh/',
          ],
        );
        final DioService service = fixture.service;
        await _signIn(service);
        expect(await service.hasSessionCookies(), isTrue);
        expect(await service.getAccessToken(), expiredCookie ? isNull : 'old');

        final response = await service.callApi<bool>(
          NetworkRequest(path: 'protected/', method: RequestMethod.get),
          mapper: (json) => json as bool,
        );
        expect(response.data, isTrue);
        expect(refreshes, 1);
        expect(protectedRequests, 2);
        expect(AccountSession.userId, 'account-a');
        expect(expirations, 0);
        expect(await service.getAccessToken(), 'fresh');

        // Socket refreshes must use the rotated refresh cookie as well.
        expect(await service.refreshSession(), isTrue);
        expect(refreshes, 2);
        expect(expirations, 0);
      },
    );
  }

  test('a persisted refresh-only session restores and refreshes', () async {
    int refreshes = 0;
    final fixture = await _service(
      (request) async {
        expect(request.uri.path, '/api/v1/auth/refresh/');
        refreshes++;
        expect(
          request.headers.value(HttpHeaders.authorizationHeader),
          'Bearer refresh',
        );
        request.response.cookies.add(Cookie('access', 'fresh')..path = '/');
        await _respond(request);
      },
      loginCookies: () => [
        Cookie('refresh', 'refresh')..path = '/api/v1/auth/refresh/',
        Cookie('logged_in', 'true')..path = '/',
      ],
    );
    await _signIn(fixture.service);
    final DioService restored = fixture.restore();
    expect(await restored.hasSessionCookies(), isTrue);
    expect(await restored.getAccessToken(), isNull);
    expect(await restored.refreshSession(), isTrue);
    expect(await restored.getAccessToken(), 'fresh');
    expect(refreshes, 1);
    expect(AccountSession.userId, 'account-a');
  });

  test(
    'socket startup refreshes a persisted session with no access cookie',
    () async {
      int refreshes = 0;
      final connected = Completer<String?>();
      final fixture = await _service(
        (request) async {
          if (request.uri.path == '/api/v1/auth/refresh/') {
            refreshes++;
            request.response.cookies.add(Cookie('access', 'fresh')..path = '/');
            return _respond(request);
          }
          expect(request.uri.path, '/ws/chat/');
          connected.complete(request.uri.queryParameters['token']);
          final WebSocket socket = await WebSocketTransformer.upgrade(request);
          socket.listen((_) {});
        },
        loginCookies: () => [
          Cookie('refresh', 'refresh')..path = '/api/v1/auth/refresh/',
        ],
      );
      await _signIn(fixture.service);
      final DioService restored = fixture.restore();
      final Uri baseUri = (await restored.getBaseUri())!;
      final client = WebSocketClientImpl<Map<String, dynamic>>(
        url: baseUri.replace(scheme: 'ws', path: '/ws/chat/'),
        accessTokenProvider: restored.getAccessToken,
        refreshAccessToken: restored.refreshSession,
        jsonToMessage: (json) => json,
        onReceiveMessage: (_) {},
      );
      addTearDown(client.disconnect);
      await client.connect();
      expect(client.isConnected, isTrue);
      expect(refreshes, 1);
      expect(
        await connected.future.timeout(const Duration(seconds: 2)),
        'fresh',
      );
      expect(AccountSession.userId, 'account-a');
    },
  );

  test(
    'socket startup with no usable refresh ends authentication once',
    () async {
      int refreshes = 0;
      final errors = <Object>[];
      final fixture = await _service(
        (request) async => fail('No authenticated connection is expected'),
        loginCookies: () => [],
      );
      await _signIn(fixture.service);
      final Uri baseUri = (await fixture.service.getBaseUri())!;
      final client = WebSocketClientImpl<Map<String, dynamic>>(
        url: baseUri.replace(scheme: 'ws', path: '/ws/chat/'),
        accessTokenProvider: fixture.service.getAccessToken,
        refreshAccessToken: () {
          refreshes++;
          return fixture.service.refreshSession();
        },
        jsonToMessage: (json) => json,
        onReceiveMessage: (_) {},
        onError: (error, _) => errors.add(error),
      );
      addTearDown(client.disconnect);
      await client.connect();
      expect(client.isConnected, isFalse);
      expect(refreshes, 1);
      expect(errors, [isA<SocketAuthenticationException>()]);
      expect(AccountSession.userId, isNull);
    },
  );

  test('unrelated and expired cookies do not restore authentication', () async {
    final fixture = await _service(
      (request) async => fail('No protected request is expected'),
      loginCookies: () => [
        Cookie('logged_in', 'true')..path = '/',
        Cookie('__cf_bm', 'unrelated')..path = '/',
        Cookie('access', 'expired')
          ..path = '/'
          ..maxAge = 0,
        Cookie('refresh', 'expired')
          ..path = '/'
          ..maxAge = 0,
      ],
    );
    await fixture.service.callApi(
      NetworkRequest(path: ApiConstants.login, method: RequestMethod.post),
    );
    expect(await fixture.service.hasSessionCookies(), isFalse);
    expect(await fixture.restore().hasSessionCookies(), isFalse);
  });

  for (final String endpoint in [
    ApiConstants.login,
    ApiConstants.googleLogin,
  ]) {
    test(
      'rejected credentials at $endpoint do not refresh an existing session',
      () async {
        int attempts = 0;
        final fixture = await _service((request) async {
          attempts++;
          expect(request.uri.path, '/api/v1/$endpoint');
          await _respond(request, status: 401);
        });
        await _signIn(fixture.service);
        await expectLater(
          fixture.service.callApi(
            NetworkRequest(
              path: endpoint,
              method: RequestMethod.post,
              queryParameters: const {'invalid': 'true'},
            ),
          ),
          throwsA(isA<UnauthorizedException>()),
        );
        expect(attempts, 1);
        expect(AccountSession.userId, 'account-a');
        expect(await fixture.service.getAccessToken(), 'old');
      },
    );
  }

  for (final int refreshStatus in [403, 429, 500]) {
    test(
      'refresh failure $refreshStatus preserves the session for recovery',
      () async {
        int refreshes = 0;
        final fixture = await _service((request) async {
          if (request.uri.path == '/api/v1/auth/refresh/') {
            refreshes++;
            if (refreshes == 1) return _respond(request, status: refreshStatus);
            request.response.cookies.add(Cookie('access', 'fresh')..path = '/');
            return _respond(request);
          }
          await _respond(
            request,
            status:
                request.headers.value(HttpHeaders.authorizationHeader) ==
                    'Bearer fresh'
                ? 200
                : 401,
          );
        });
        final DioService service = fixture.service;
        await _signIn(service);
        await expectLater(
          service.callApi(
            NetworkRequest(path: 'protected/', method: RequestMethod.get),
          ),
          throwsA(isA<ServerException>()),
        );
        expect(refreshes, 1);
        expect(AccountSession.userId, 'account-a');
        expect(await service.hasSessionCookies(), isTrue);
        await service.callApi(
          NetworkRequest(path: 'protected/', method: RequestMethod.get),
        );
        expect(refreshes, 2);
        expect(AccountSession.userId, 'account-a');
      },
    );
  }

  test('an offline refresh keeps the session and can recover', () async {
    final adapter = _OfflineRefreshAdapter();
    addTearDown(() => adapter.close(force: true));
    int refreshes = 0;
    final fixture = await _service((request) async {
      if (request.uri.path == '/api/v1/auth/refresh/') {
        refreshes++;
        request.response.cookies.add(Cookie('access', 'fresh')..path = '/');
        return _respond(request);
      }
      await _respond(
        request,
        status:
            request.headers.value(HttpHeaders.authorizationHeader) ==
                'Bearer fresh'
            ? 200
            : 401,
      );
    }, httpClientAdapter: adapter);
    await _signIn(fixture.service);
    await expectLater(
      fixture.service.callApi(
        NetworkRequest(path: 'protected/', method: RequestMethod.get),
      ),
      throwsA(isA<NoInternetConnectionException>()),
    );
    expect(refreshes, 0);
    expect(AccountSession.userId, 'account-a');
    expect(await fixture.service.hasSessionCookies(), isTrue);
    adapter.isOffline = false;
    await fixture.service.callApi(
      NetworkRequest(path: 'protected/', method: RequestMethod.get),
    );
    expect(refreshes, 1);
    expect(AccountSession.userId, 'account-a');
  });

  test(
    'a rejected refresh expires once without retrying the original request',
    () async {
      int refreshes = 0;
      int protectedRequests = 0;
      int expirations = 0;
      final subscription = AccountSession.expired.listen((_) => expirations++);
      addTearDown(subscription.cancel);
      final fixture = await _service((request) async {
        if (request.uri.path == '/api/v1/auth/refresh/') {
          refreshes++;
        } else {
          protectedRequests++;
        }
        await _respond(request, status: 401);
      });
      await _signIn(fixture.service);
      await expectLater(
        fixture.service.callApi(
          NetworkRequest(path: 'protected/', method: RequestMethod.get),
        ),
        throwsA(isA<UnauthorizedException>()),
      );
      expect(refreshes, 1);
      expect(protectedRequests, 1);
      expect(expirations, 1);
      expect(AccountSession.userId, isNull);
      expect(await fixture.service.hasSessionCookies(), isFalse);
    },
  );

  test(
    'socket refresh with no refresh token expires the signed-in session',
    () async {
      final fixture = await _service(
        (request) async => fail('No refresh token should reach the backend'),
        loginCookies: () => [Cookie('access', 'old')..path = '/'],
      );
      await _signIn(fixture.service);
      expect(await fixture.service.refreshSession(), isFalse);
      expect(AccountSession.userId, isNull);
      expect(await fixture.service.hasSessionCookies(), isFalse);
    },
  );
}

Future<({DioService service, DioService Function() restore})> _service(
  Future<void> Function(HttpRequest) handler, {
  List<Cookie> Function()? loginCookies,
  HttpClientAdapter? httpClientAdapter,
}) async {
  final Directory directory = await Directory.systemTemp.createTemp(
    'backend_session_',
  );
  final HttpServer server = await HttpServer.bind(
    InternetAddress.loopbackIPv4,
    0,
  );
  addTearDown(() async {
    await server.close(force: true);
    await directory.delete(recursive: true);
  });
  server.listen((request) async {
    if (request.uri.path == '/api/v1/auth/login/' &&
        request.uri.queryParameters['invalid'] != 'true') {
      request.response.cookies.addAll(
        loginCookies?.call() ??
            [
              Cookie('access', 'old')..path = '/',
              Cookie('refresh', 'refresh')..path = '/',
            ],
      );
      await _respond(request);
    } else {
      try {
        await handler(request);
      } catch (_) {
        // Failed server assertions must finish the request instead of timing out.
        await request.response.close();
        rethrow;
      }
    }
  });
  DioService createService() => DioService(
    initialBaseUrl: 'http://${server.address.host}:${server.port}/api/v1/',
    initialLanguageCode: 'en',
    cookieDirectoryProvider: () async => directory,
    httpClientAdapter: httpClientAdapter,
  );
  return (service: createService(), restore: createService);
}

Future<void> _signIn(DioService service) async {
  await service.callApi(
    NetworkRequest(path: ApiConstants.login, method: RequestMethod.post),
  );
  AccountSession.begin('account-a');
}

Future<void> _respond(HttpRequest request, {int status = 200}) async {
  request.response
    ..statusCode = status
    ..headers.contentType = ContentType.json
    ..write(jsonEncode({'data': true, 'message': 'Test response'}));
  await request.response.close();
}

class _OfflineRefreshAdapter extends IOHttpClientAdapter {
  bool isOffline = true;

  @override
  Future<ResponseBody> fetch(
    RequestOptions options,
    Stream<Uint8List>? requestStream,
    Future<void>? cancelFuture,
  ) {
    if (isOffline && options.uri.path == '/api/v1/auth/refresh/') {
      throw DioException(
        requestOptions: options,
        type: DioExceptionType.connectionError,
        error: const SocketException('Offline during refresh'),
      );
    }
    return super.fetch(options, requestStream, cancelFuture);
  }
}
