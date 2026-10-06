import 'dart:convert';
import 'dart:io';
import 'dart:typed_data';

import 'package:dio/dio.dart';
import 'package:easy_localization/easy_localization.dart';
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:melos_core/config/language/languages.dart';
import 'package:melos_core/core/navigation/navigator.dart';
import 'package:melos_core/core/network/dio_service.dart';
import 'package:melos_core/core/network/network_request.dart';
import 'package:shared_preferences/shared_preferences.dart';

void main() {
  TestWidgetsFlutterBinding.ensureInitialized();

  test('shared headers reach reads and JSON writes', () async {
    final adapter = _RecordingAdapter();
    final service = await _service(adapter);

    await service.callApi(
      NetworkRequest(path: 'read/', method: RequestMethod.get),
    );
    await service.callApi(
      NetworkRequest(
        path: 'write/',
        method: RequestMethod.post,
        body: {'message': 'hello'},
      ),
    );

    for (final request in adapter.requests) {
      expect(
        request.headers[HttpHeaders.acceptHeader],
        Headers.jsonContentType,
      );
      expect(request.headers[HttpHeaders.acceptLanguageHeader], 'en');
      expect(request.contentType, Headers.jsonContentType);
    }
    expect(jsonDecode(adapter.bodies.last), {'message': 'hello'});
  });

  test('explicit headers override defaults regardless of casing', () async {
    final adapter = _RecordingAdapter();
    final service = await _service(adapter);

    await service.callApi(
      NetworkRequest(
        path: 'custom/',
        method: RequestMethod.get,
        headers: {
          'Accept': 'application/problem+json',
          'Accept-Language': 'ar',
          'Content-Type': 'text/plain',
          'X-Request-Id': 'request-1',
        },
      ),
    );

    final request = adapter.requests.single;
    expect(
      request.headers[HttpHeaders.acceptHeader],
      'application/problem+json',
    );
    expect(request.headers[HttpHeaders.acceptLanguageHeader], 'ar');
    expect(request.contentType, 'text/plain');
    expect(request.headers['x-request-id'], 'request-1');
  });

  test(
    'uploads retain multipart boundaries and repeated attachment fields',
    () async {
      final directory = await Directory.systemTemp.createTemp('header_upload_');
      addTearDown(() => directory.delete(recursive: true));
      final jpg = await File(
        '${directory.path}/first.jpg',
      ).writeAsString('first');
      final png = await File(
        '${directory.path}/second.png',
      ).writeAsString('second');
      final adapter = _RecordingAdapter();
      final service = await _service(adapter);

      await service.callApi(
        NetworkRequest(
          path: 'upload/',
          method: RequestMethod.post,
          body: {
            'workspace': 'tenant',
            'attachments': [jpg, png],
          },
        ),
      );

      final contentType = ContentType.parse(
        adapter.requests.single.contentType!,
      );
      expect(contentType.mimeType, Headers.multipartFormDataContentType);
      expect(contentType.parameters['boundary'], isNotEmpty);
      expect(
        adapter.bodies.single,
        contains('--${contentType.parameters['boundary']}'),
      );
      expect('name="attachments"'.allMatches(adapter.bodies.single).length, 2);
      expect(adapter.bodies.single, contains('image/jpeg'));
      expect(adapter.bodies.single, contains('image/png'));
    },
  );

  testWidgets(
    'the same service sends the current language after a locale change',
    (tester) async {
      SharedPreferences.setMockInitialValues({});
      await EasyLocalization.ensureInitialized();
      final adapter = _RecordingAdapter();
      final service = (await tester.runAsync(
        () => _service(adapter, languageCode: null),
      ))!;

      await tester.pumpWidget(
        EasyLocalization(
          supportedLocales: Languages.supportedLocales,
          path: 'translations',
          assetLoader: const _EmptyTranslations(),
          startLocale: Languages.english.locale,
          fallbackLocale: Languages.english.locale,
          saveLocale: false,
          child: Builder(
            builder: (context) => MaterialApp(
              navigatorKey: Go.navigatorKey,
              localizationsDelegates: context.localizationDelegates,
              supportedLocales: context.supportedLocales,
              locale: context.locale,
              home: const SizedBox.shrink(),
            ),
          ),
        ),
      );
      await tester.pumpAndSettle();

      await tester.runAsync(
        () => service.callApi(
          NetworkRequest(path: 'english/', method: RequestMethod.get),
        ),
      );
      await Go.context.setLocale(Languages.arabic.locale);
      await tester.pumpAndSettle();
      await tester.runAsync(
        () => service.callApi(
          NetworkRequest(path: 'arabic/', method: RequestMethod.get),
        ),
      );

      expect(
        adapter.requests.map(
          (request) => request.headers[HttpHeaders.acceptLanguageHeader],
        ),
        ['en', 'ar'],
      );
      expect(tester.takeException(), isNull);
    },
  );
}

Future<DioService> _service(
  _RecordingAdapter adapter, {
  String? languageCode = 'en',
}) async {
  final directory = await Directory.systemTemp.createTemp('request_headers_');
  addTearDown(() => directory.delete(recursive: true));
  return DioService(
    initialBaseUrl: 'https://example.invalid/api/v1/',
    initialLanguageCode: languageCode,
    cookieDirectoryProvider: () async => directory,
    httpClientAdapter: adapter,
  );
}

class _RecordingAdapter implements HttpClientAdapter {
  final requests = <RequestOptions>[];
  final bodies = <String>[];

  @override
  Future<ResponseBody> fetch(
    RequestOptions options,
    Stream<Uint8List>? requestStream,
    Future<void>? cancelFuture,
  ) async {
    requests.add(options);
    bodies.add(
      await requestStream?.cast<List<int>>().transform(utf8.decoder).join() ??
          '',
    );
    return ResponseBody.fromString(
      '{"key":"success","message":"","data":true}',
      200,
      headers: {
        Headers.contentTypeHeader: [Headers.jsonContentType],
      },
    );
  }

  @override
  void close({bool force = false}) {}
}

class _EmptyTranslations extends AssetLoader {
  const _EmptyTranslations();

  @override
  Future<Map<String, dynamic>> load(String path, Locale locale) async => {};
}
