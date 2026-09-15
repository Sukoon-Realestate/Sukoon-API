import 'dart:convert';
import 'dart:io';

import 'package:flutter_test/flutter_test.dart';
import 'package:melos_core/core/network/dio_service.dart';
import 'package:melos_core/core/network/network_request.dart';

void main() {
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
