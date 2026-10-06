import 'dart:async';
import 'dart:convert';
import 'dart:io';
import 'dart:typed_data';

import 'package:dio/dio.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:melos_core/core/error/exceptions.dart';
import 'package:melos_core/core/network/account_session.dart';
import 'package:melos_core/core/network/dio_service.dart';
import 'package:melos_core/core/network/network_request.dart';

void main() {
  setUp(AccountSession.end);
  tearDown(AccountSession.end);

  for (final bool socketFirst in [false, true]) {
    test('HTTP and socket share refresh, socket first: $socketFirst', () async {
      final refreshing = Completer<void>();
      final release = Completer<void>();
      final bothRejected = Completer<void>();
      int refreshes = 0;
      int rejected = 0;
      int retries = 0;
      final service = await _service((request) async {
        if (request.uri.path == '/auth/refresh/') {
          refreshes++;
          if (!refreshing.isCompleted) refreshing.complete();
          await release.future;
          return _respond(request, fresh: true);
        }
        if (request.headers.value(HttpHeaders.authorizationHeader) ==
            'Bearer old') {
          rejected++;
          await _respond(request, status: 401);
          if (rejected == 2 && !bothRejected.isCompleted) {
            bothRejected.complete();
          }
        } else {
          retries++;
          await _respond(request);
        }
      });
      await _signIn(service);
      Future<bool>? socket;
      if (socketFirst) {
        socket = service.refreshSession();
        await refreshing.future;
      }
      final first = service.callApi(
        NetworkRequest(path: 'first/', method: RequestMethod.get),
      );
      final second = service.callApi(
        NetworkRequest(path: 'second/', method: RequestMethod.get),
      );
      await bothRejected.future;
      await refreshing.future;
      socket ??= service.refreshSession();
      release.complete();
      await Future.wait([first, second]);
      expect(await socket, isTrue);
      expect(refreshes, 1);
      expect(retries, 2);
      expect(await service.getAccessToken(), 'fresh');
    });
  }

  test('late 401 reuses an already refreshed token', () async {
    final received = Completer<void>();
    final release = Completer<void>();
    int refreshes = 0;
    int protected = 0;
    final service = await _service((request) async {
      if (request.uri.path == '/auth/refresh/') {
        refreshes++;
        return _respond(request, fresh: true);
      }
      protected++;
      if (protected == 1) {
        received.complete();
        await release.future;
        return _respond(request, status: 401);
      }
      expect(
        request.headers.value(HttpHeaders.authorizationHeader),
        'Bearer fresh',
      );
      await _respond(request);
    });
    await _signIn(service);
    final pending = service.callApi(
      NetworkRequest(path: 'late/', method: RequestMethod.get),
    );
    await received.future;
    expect(await service.refreshSession(), isTrue);
    release.complete();
    await pending;
    expect(refreshes, 1);
    expect(protected, 2);
  });

  test(
    'cancelling an HTTP waiter leaves shared refresh and other callers alive',
    () async {
      final refreshing = Completer<void>();
      final release = Completer<void>();
      final received = Completer<void>();
      int refreshes = 0;
      int cancelledCalls = 0;
      final service = await _service((request) async {
        if (request.uri.path == '/auth/refresh/') {
          refreshes++;
          refreshing.complete();
          await release.future;
          return _respond(request, fresh: true);
        }
        if (request.uri.path == '/cancel/') {
          cancelledCalls++;
          await _respond(request, status: 401);
          received.complete();
          return;
        }
        await _respond(
          request,
          status:
              request.headers.value(HttpHeaders.authorizationHeader) ==
                  'Bearer old'
              ? 401
              : 200,
        );
      });
      await _signIn(service);
      final socket = service.refreshSession();
      await refreshing.future;
      final token = CancelToken();
      final cancelled = service.callApi(
        NetworkRequest(
          path: 'cancel/',
          method: RequestMethod.get,
          cancelToken: token,
        ),
      );
      final checked = expectLater(
        cancelled,
        throwsA(isA<RequestCancelledException>()),
      );
      final other = service.callApi(
        NetworkRequest(path: 'other/', method: RequestMethod.get),
      );
      await received.future;
      token.cancel();
      await checked.timeout(const Duration(seconds: 2));
      release.complete();
      expect(await socket, isTrue);
      await other;
      expect(refreshes, 1);
      expect(cancelledCalls, 1);
      expect(AccountSession.userId, 'a');
    },
  );

  for (final int status in [401, 500]) {
    test(
      'shared refresh $status has consistent expiry and can recover',
      () async {
        int refreshes = 0;
        final service = await _service((request) async {
          refreshes++;
          await _respond(
            request,
            status: refreshes == 1 ? status : 200,
            fresh: refreshes > 1,
          );
        });
        await _signIn(service);
        final results = await Future.wait([
          service.refreshSession(),
          service.refreshSession(),
        ]);
        expect(results, [false, false]);
        expect(refreshes, 1);
        expect(AccountSession.userId, status == 401 ? isNull : 'a');
        if (status == 500) {
          expect(await service.refreshSession(), isTrue);
          expect(refreshes, 2);
        }
      },
    );
  }

  test(
    'multipart uploads replay once after refresh with their file intact',
    () async {
      final bodies = <String>[];
      int refreshes = 0;
      final service = await _service((request) async {
        if (request.uri.path == '/auth/refresh/') {
          refreshes++;
          return _respond(request, fresh: true);
        }
        bodies.add(await utf8.decoder.bind(request).join());
        await _respond(request, status: bodies.length == 1 ? 401 : 200);
      });
      await _signIn(service);
      await service.callApi(
        NetworkRequest(
          path: 'upload/',
          method: RequestMethod.post,
          isFormData: true,
          body: {
            'file': MultipartFile.fromString(
              'uploaded content',
              filename: 'test.txt',
            ),
          },
          sendTimeout: const Duration(minutes: 5),
        ),
      );
      expect(refreshes, 1);
      expect(bodies, hasLength(2));
      expect(bodies.every((body) => body.contains('uploaded content')), isTrue);
    },
  );

  test('a rejected retry expires once without a refresh loop', () async {
    int refreshes = 0;
    int calls = 0;
    int expirations = 0;
    final subscription = AccountSession.expired.listen((_) => expirations++);
    addTearDown(subscription.cancel);
    final service = await _service((request) async {
      if (request.uri.path == '/auth/refresh/') {
        refreshes++;
        return _respond(request, fresh: true);
      }
      calls++;
      await _respond(request, status: 401);
    });
    await _signIn(service);
    await expectLater(
      service.callApi(
        NetworkRequest(path: 'protected/', method: RequestMethod.get),
      ),
      throwsA(isA<UnauthorizedException>()),
    );
    expect(refreshes, 1);
    expect(calls, 2);
    expect(AccountSession.userId, isNull);
    expect(expirations, 1);
  });

  test('GET reports byte progress before the response completes', () async {
    final progress = Completer<void>();
    final release = Completer<void>();
    final bytes = utf8.encode(jsonEncode({'data': 'x' * 128000}));
    final service = await _service((request) async {
      request.response.headers.contentType = ContentType.json;
      request.response.contentLength = bytes.length;
      request.response.add(bytes.sublist(0, 64000));
      await request.response.flush();
      await release.future;
      request.response.add(bytes.sublist(64000));
      await request.response.close();
    });
    final updates = <(int, int)>[];
    final response = service.callApi<String>(
      NetworkRequest(
        path: 'download/',
        method: RequestMethod.get,
        onReceiveProgress: (received, total) {
          updates.add((received, total));
          if (!progress.isCompleted) progress.complete();
        },
      ),
      mapper: (json) => json as String,
    );
    await progress.future.timeout(const Duration(seconds: 2));
    expect(updates.first.$1, lessThan(bytes.length));
    release.complete();
    expect((await response).data.length, 128000);
    expect(updates.last, (bytes.length, bytes.length));
  });

  test('cancellation stops a live GET without expiring the account', () async {
    final received = Completer<void>();
    final release = Completer<void>();
    final service = await _service((request) async {
      received.complete();
      await release.future;
      await _respond(request);
    });
    await _signIn(service);
    final token = CancelToken();
    final pending = service.callApi(
      NetworkRequest(
        path: 'slow/',
        method: RequestMethod.get,
        cancelToken: token,
      ),
    );
    final checked = expectLater(
      pending,
      throwsA(isA<RequestCancelledException>()),
    );
    await received.future;
    token.cancel();
    await checked.timeout(const Duration(seconds: 2));
    expect(AccountSession.userId, 'a');
    release.complete();
  });

  test(
    'cancelled requests never reach the adapter; send timeouts can be overridden',
    () async {
      final directory = await Directory.systemTemp.createTemp(
        'request_options_',
      );
      addTearDown(() => directory.delete(recursive: true));
      final adapter = _RecordingAdapter();
      final service = DioService(
        initialBaseUrl: 'https://example.com/',
        initialLanguageCode: 'en',
        cookieDirectoryProvider: () async => directory,
        httpClientAdapter: adapter,
      );
      final cancelled = CancelToken()..cancel();
      await expectLater(
        service.callApi(
          NetworkRequest(
            path: 'cancel/',
            method: RequestMethod.get,
            cancelToken: cancelled,
          ),
        ),
        throwsA(isA<RequestCancelledException>()),
      );
      expect(adapter.requests, isEmpty);
      await service.callApi(
        NetworkRequest(path: 'default/', method: RequestMethod.get),
      );
      await service.callApi(
        NetworkRequest(
          path: 'upload/',
          method: RequestMethod.post,
          body: {'file': 'data'},
          sendTimeout: const Duration(minutes: 5),
        ),
      );
      expect(adapter.requests.map((request) => request.sendTimeout), [
        const Duration(seconds: 120),
        const Duration(minutes: 5),
      ]);
      adapter.timeout = true;
      await expectLater(
        service.callApi(
          NetworkRequest(path: 'timeout/', method: RequestMethod.post),
        ),
        throwsA(isA<NoInternetConnectionException>()),
      );
    },
  );
}

Future<DioService> _service(Future<void> Function(HttpRequest) handler) async {
  final directory = await Directory.systemTemp.createTemp('request_controls_');
  final server = await HttpServer.bind(InternetAddress.loopbackIPv4, 0);
  addTearDown(() async {
    await server.close(force: true);
    await directory.delete(recursive: true);
  });
  server.listen((request) async {
    if (request.uri.path == '/login/') {
      request.response.cookies
        ..add(Cookie('access_token', 'old')..path = '/')
        ..add(Cookie('refresh_token', 'refresh')..path = '/');
      await _respond(request);
    } else {
      await handler(request);
    }
  });
  return DioService(
    initialBaseUrl: 'http://${server.address.host}:${server.port}/',
    initialLanguageCode: 'en',
    cookieDirectoryProvider: () async => directory,
  );
}

Future<void> _signIn(DioService service) async {
  await service.callApi(
    NetworkRequest(path: 'login/', method: RequestMethod.post),
  );
  AccountSession.begin('a');
}

Future<void> _respond(
  HttpRequest request, {
  int status = 200,
  bool fresh = false,
}) async {
  request.response.headers.contentType = ContentType.json;
  request.response.statusCode = status;
  if (fresh) {
    request.response.cookies.add(Cookie('access_token', 'fresh')..path = '/');
  }
  request.response.write(jsonEncode({'data': true}));
  await request.response.close();
}

class _RecordingAdapter implements HttpClientAdapter {
  final requests = <RequestOptions>[];
  bool timeout = false;

  @override
  Future<ResponseBody> fetch(
    RequestOptions options,
    Stream<Uint8List>? requestStream,
    Future<void>? cancelFuture,
  ) async {
    requests.add(options);
    if (timeout) {
      throw DioException(
        requestOptions: options,
        type: DioExceptionType.sendTimeout,
      );
    }
    return ResponseBody.fromString(
      '{"data":true}',
      200,
      headers: {
        Headers.contentTypeHeader: [Headers.jsonContentType],
      },
    );
  }

  @override
  void close({bool force = false}) {}
}
