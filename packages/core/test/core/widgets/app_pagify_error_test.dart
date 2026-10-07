import 'dart:async';

import 'package:easy_localization/easy_localization.dart';
import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:melos_core/config/language/locale_keys.g.dart';
import 'package:melos_core/core/error/exceptions.dart';
import 'package:melos_core/core/network/account_session.dart';
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
    'refreshing an outgoing page after logout does not dispatch a request',
    (tester) async {
      AccountSession.begin('signed-in-user');
      addTearDown(AccountSession.end);
      final controller = PagifyController<String>();
      int requests = 0;
      await tester.pumpWidget(
        _screen(
          AppPagify<String>(
            pagifyController: controller,
            loadingBuilder: const SizedBox.shrink(),
            asyncCall: (_, _) async {
              requests++;
              return (
                ['Loaded result'],
                PaginationData(perPage: 10, totalPages: 1),
              );
            },
            itemBuilder: (_, _, _, item) => Text(item),
          ),
        ),
      );
      await tester.pumpAndSettle();
      expect(requests, 1);

      AccountSession.end();
      controller.refresh();
      await tester.pumpAndSettle();
      expect(requests, 1);
      expect(tester.takeException(), isNull);
      await tester.pumpWidget(const SizedBox.shrink());
    },
  );

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

  testWidgets(
    'keeps previous results through a failed replacement and retries',
    (tester) async {
      final controller = PagifyController<String>();
      final requests = <Completer<(List<String>, PaginationData)>>[];
      await tester.pumpWidget(
        _screen(
          AppPagify<String>(
            pagifyController: controller,
            shrinkWrap: false,
            retainItemsOnRefresh: true,
            onError: (_, _, _) {},
            retainedItemsNotice: (isLoading, retry) => isLoading
                ? const Text('Updating previous results')
                : TextButton(
                    onPressed: retry,
                    child: const Text('Retry previous results'),
                  ),
            loadingBuilder: const SizedBox.shrink(),
            asyncCall: (_, _) {
              final request = Completer<(List<String>, PaginationData)>();
              requests.add(request);
              return request.future;
            },
            itemBuilder: (_, _, _, item) => Text(item),
          ),
        ),
      );
      await tester.pumpAndSettle();
      requests.single.complete((
        ['Previous result'],
        PaginationData(perPage: 10, totalPages: 1),
      ));
      await tester.pumpAndSettle();
      controller.refresh();
      await tester.pumpAndSettle();
      expect(find.text('Previous result'), findsOneWidget);
      expect(find.text('Updating previous results'), findsOneWidget);
      requests.last.completeError(ServerException('Replacement failed'));
      await tester.pumpAndSettle();
      expect(find.text('Previous result'), findsOneWidget);
      await tester.tap(find.text('Retry previous results'));
      await tester.pumpAndSettle();
      requests.last.complete((
        ['New result'],
        PaginationData(perPage: 10, totalPages: 1),
      ));
      await tester.pumpAndSettle();
      expect(controller.items, ['New result']);
      expect(find.text('Previous result'), findsNothing);
      expect(find.text('New result'), findsOneWidget);
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
  testWidgets(
    'a filtered pagination failure retries the same page without losing source items',
    (tester) async {
      final controller = PagifyController<String>();
      final requests = <int>[];
      bool failNextPage = true;
      String? message;
      await tester.pumpWidget(
        _screen(
          AppPagify<String>(
            pagifyController: controller,
            loadingBuilder: const SizedBox.shrink(),
            onError: (_, _, error) => message = error.msg,
            filterItems: (items) =>
                items.where((item) => item == 'bed').toList(),
            emptyListView: const Text('No matching loaded accommodation'),
            filteredFooterBuilder:
                (context, hasMore, isLoading, error, loadMore) => hasMore
                ? TextButton(
                    onPressed: isLoading ? null : loadMore,
                    child: Text(error ?? 'Next page'),
                  )
                : const SizedBox.shrink(),
            asyncCall: (_, page) async {
              requests.add(page);
              if (page == 2 && failNextPage) {
                failNextPage = false;
                throw const ServerException('Bed page unavailable');
              }
              return (
                [page == 1 ? 'room' : 'bed'],
                PaginationData(perPage: 1, totalPages: 2),
              );
            },
            itemBuilder: (_, _, _, item) => Text(item),
          ),
        ),
      );
      await tester.pumpAndSettle();
      await tester.tap(find.text('Next page'));
      await tester.pumpAndSettle();
      expect(message, 'Bed page unavailable');
      expect(controller.items, ['room']);
      expect(find.text('Bed page unavailable'), findsOneWidget);
      await tester.tap(find.text('Bed page unavailable'));
      await tester.pumpAndSettle();
      expect(requests, [1, 2, 2]);
      expect(controller.items, ['room', 'bed']);
      expect(find.text('bed'), findsOneWidget);
      expect(tester.takeException(), isNull);
    },
  );
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
