import 'dart:async';

import 'package:easy_localization/easy_localization.dart';
import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:melos_core/config/language/locale_keys.g.dart';
import 'package:melos_core/core/error/exceptions.dart';
import 'package:melos_core/core/widgets/app_pagify.dart';
import 'package:melos_core/core/widgets/exeption_view.dart';
import 'package:melos_core/core/widgets/retry_view.dart';
import 'package:pagify/helpers/data_and_pagination_data.dart';
import 'package:pagify/helpers/errors.dart';
import 'package:pagify/pagify.dart';

void main() {
  TestWidgetsFlutterBinding.ensureInitialized();
  final messenger =
      TestDefaultBinaryMessengerBinding.instance.defaultBinaryMessenger;
  const preferencesChannel = MethodChannel(
    'plugins.flutter.io/shared_preferences',
  );
  const connectivityChannel = MethodChannel(
    'dev.fluttercommunity.plus/connectivity',
  );
  bool connected = true;

  setUpAll(() async {
    messenger.setMockMethodCallHandler(
      preferencesChannel,
      (call) async => call.method == 'getAll' ? <String, Object>{} : true,
    );
    messenger.setMockMethodCallHandler(
      connectivityChannel,
      (_) async => [connected ? 'wifi' : 'none'],
    );
    await EasyLocalization.ensureInitialized();
  });

  setUp(() => connected = true);

  tearDownAll(() {
    messenger.setMockMethodCallHandler(preferencesChannel, null);
    messenger.setMockMethodCallHandler(connectivityChannel, null);
  });

  testWidgets(
    'cancelled pages do not display errors or notify error listeners',
    (tester) async {
      final controller = PagifyController<String>();
      final request = Completer<(List<String>, PaginationData)>();
      final errors = <PagifyException>[];
      await tester.pumpWidget(
        _screen(
          AppPagify<String>(
            pagifyController: controller,
            shrinkWrap: false,
            loadingBuilder: const SizedBox.shrink(),
            onError: (_, _, error) => errors.add(error),
            asyncCall: (_, __) => request.future,
            itemBuilder: (_, _, _, item) => Text(item),
          ),
        ),
      );
      await tester.pumpAndSettle();
      request.completeError(const RequestCancelledException());
      await tester.pumpAndSettle();
      expect(errors, isEmpty);
      expect(find.byType(ExceptionView), findsNothing);
      expect(tester.takeException(), isNull);
      await tester.pumpWidget(const SizedBox.shrink());
    },
  );

  for (final Ranking ranking in Ranking.values) {
    for (final String kind in ['connection', 'server', 'pagify']) {
      testWidgets(
        '$ranking preserves $kind messages and retries the failed page',
        (tester) async {
          final controller = PagifyController<String>();
          final requests = <Completer<(List<String>, PaginationData)>>[];
          final pages = <int>[];
          final errors = <PagifyException>[];
          await tester.pumpWidget(
            _screen(
              AppPagify<String>(
                pagifyController: controller,
                rankingType: ranking,
                shrinkWrap: false,
                loadingBuilder: const SizedBox.shrink(),
                onError: (_, _, error) => errors.add(error),
                asyncCall: (_, page) {
                  pages.add(page);
                  final request = Completer<(List<String>, PaginationData)>();
                  requests.add(request);
                  return request.future;
                },
                itemBuilder: (_, _, _, item) => Text(item),
              ),
            ),
          );
          await tester.pumpAndSettle();
          final String message = kind == 'connection'
              ? LocaleKeys.checkInternet
              : 'The server could not load these results';
          final Exception error = switch (kind) {
            'connection' => NoInternetConnectionException(' $message '),
            'pagify' => PagifyApiRequestException(
              message,
              pagifyFailure: RequestFailureData.initial(),
            ),
            _ => ServerException(message),
          };
          requests.single.completeError(error);
          await tester.pumpAndSettle();

          expect(find.byType(ExceptionView), findsOneWidget);
          expect(
            find.byType(AppRetryView),
            kind == 'connection' ? findsOneWidget : findsNothing,
          );
          expect(find.text(message), findsOneWidget);
          expect(errors.single.msg.trim(), message);

          await tester.tap(find.text(LocaleKeys.ownerRetryAction));
          await tester.pumpAndSettle();
          expect(pages, [1, 1]);
          requests.last.complete((
            ['Restored result'],
            PaginationData(perPage: 10, totalPages: 1),
          ));
          await tester.pumpAndSettle();

          expect(controller.items, ['Restored result']);
          expect(find.text('Restored result'), findsOneWidget);
          expect(find.byType(ExceptionView), findsNothing);
          expect(tester.takeException(), isNull);
          await tester.pumpWidget(const SizedBox.shrink());
        },
      );
    }

    testWidgets('$ranking retries after connectivity preflight fails', (
      tester,
    ) async {
      connected = false;
      int requests = 0;
      await tester.pumpWidget(
        _screen(
          AppPagify<String>(
            pagifyController: PagifyController<String>(),
            rankingType: ranking,
            loadingBuilder: const SizedBox.shrink(),
            onError: (_, _, _) {},
            asyncCall: (_, _) async {
              requests++;
              return (
                ['Connected result'],
                PaginationData(perPage: 10, totalPages: 1),
              );
            },
            itemBuilder: (_, _, _, item) => Text(item),
          ),
        ),
      );
      await tester.pumpAndSettle();
      expect(requests, 0);
      expect(find.byType(AppRetryView), findsOneWidget);

      connected = true;
      await tester.tap(find.text(LocaleKeys.ownerRetryAction));
      await tester.pumpAndSettle();
      expect(requests, 1);
      expect(find.text('Connected result'), findsOneWidget);
      expect(tester.takeException(), isNull);
      await tester.pumpWidget(const SizedBox.shrink());
    });
  }
}

Widget _screen(Widget child) => EasyLocalization(
  supportedLocales: const [Locale('en')],
  path: 'unused',
  assetLoader: const _Translations(),
  startLocale: const Locale('en'),
  child: ScreenUtilInit(
    designSize: const Size(390, 844),
    builder: (context, _) => MaterialApp(
      localizationsDelegates: context.localizationDelegates,
      supportedLocales: context.supportedLocales,
      locale: context.locale,
      home: Scaffold(body: child),
    ),
  ),
);

class _Translations extends AssetLoader {
  const _Translations();

  @override
  Future<Map<String, dynamic>> load(String path, Locale locale) async => {
    'check_internet': 'Please check your internet connection',
    'exception_error': 'Something went wrong',
    'owner_retry_action': 'Retry',
  };
}
