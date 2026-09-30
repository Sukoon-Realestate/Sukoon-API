import 'dart:async';

import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:melos_core/core/extensions/widget_extension.dart';
import 'package:melos_core/core/widgets/app_pagify.dart';
import 'package:pagify/helpers/data_and_pagination_data.dart';
import 'package:pagify/pagify.dart';

void main() {
  TestWidgetsFlutterBinding.ensureInitialized();
  setUpAll(() {
    final messenger =
        TestDefaultBinaryMessengerBinding.instance.defaultBinaryMessenger;
    messenger.setMockMethodCallHandler(
      const MethodChannel('dev.fluttercommunity.plus/connectivity'),
      (_) async => ['wifi'],
    );
    messenger.setMockMethodCallHandler(
      const MethodChannel('dev.fluttercommunity.plus/connectivity_status'),
      (_) async => null,
    );
  });
  testWidgets(
    'the shared extension refreshes content shorter than the screen',
    (tester) async {
      final pending = Completer<void>();
      int calls = 0;
      await tester.pumpWidget(
        _app(
          SingleChildScrollView(
            child: const SizedBox(height: 40, child: Text('Short content')),
          ).withPullRefresher(
            onRefresh: () {
              calls++;
              return pending.future;
            },
          ),
        ),
      );
      await _pull(tester);
      expect(calls, 1);
      expect(find.byType(RefreshProgressIndicator), findsOneWidget);
      pending.complete();
      await tester.pumpAndSettle();
      expect(find.byType(RefreshProgressIndicator), findsNothing);
      expect(tester.takeException(), isNull);
    },
  );

  for (final initialState in ['short', 'empty', 'error', 'header-empty']) {
    testWidgets(
      'paginated $initialState content can be pulled and waits for data',
      (tester) async {
        final pending = Completer<(List<int>, PaginationData)>();
        final pages = <int>[];
        await tester.pumpWidget(
          _app(
            _collection(
              header: initialState == 'header-empty'
                  ? const Text('Header')
                  : null,
              load: (_, page) {
                pages.add(page);
                if (pages.length > 1) return pending.future;
                if (initialState == 'error') {
                  return Future.error(Exception('Offline'));
                }
                return Future.value(_page(initialState == 'short' ? [1] : []));
              },
            ),
          ),
        );
        await tester.pumpAndSettle();
        expect(tester.takeException(), isNull);
        await _pull(tester);
        expect(pages, [1, 1]);
        expect(find.byType(RefreshProgressIndicator), findsOneWidget);
        bool finished = false;
        final waiting = tester
            .widget<RefreshIndicator>(find.byType(RefreshIndicator))
            .onRefresh()
            .then((_) => finished = true);
        await tester.pump(const Duration(seconds: 1));
        expect(finished, isFalse);
        expect(pages, [1, 1]);
        pending.complete(_page([2]));
        await tester.pumpAndSettle();
        await waiting;
        expect(find.text('Item 2'), findsOneWidget);
        expect(finished, isTrue);
        expect(find.byType(RefreshProgressIndicator), findsNothing);
        expect(tester.takeException(), isNull);
      },
    );
  }

  testWidgets('a failed refresh stops the indicator and can be pulled again', (
    tester,
  ) async {
    final pending = Completer<(List<int>, PaginationData)>();
    int calls = 0;
    await tester.pumpWidget(
      _app(
        _collection(
          load: (_, page) {
            calls++;
            return calls == 2 ? pending.future : Future.value(_page([calls]));
          },
        ),
      ),
    );
    await tester.pumpAndSettle();
    await _pull(tester);
    pending.completeError(Exception('Refresh failed'));
    await tester.pumpAndSettle();
    expect(find.byType(RefreshProgressIndicator), findsNothing);
    expect(find.text('Request failed'), findsOneWidget);
    await _pull(tester);
    await tester.pumpAndSettle();
    expect(calls, 3);
    expect(find.text('Item 3'), findsOneWidget);
    expect(tester.takeException(), isNull);
  });

  testWidgets('leaving a paginated screen releases an in-flight refresh', (
    tester,
  ) async {
    final pending = Completer<(List<int>, PaginationData)>();
    int calls = 0;
    await tester.pumpWidget(
      _app(
        _collection(
          load: (_, page) {
            calls++;
            return calls == 1 ? Future.value(_page([1])) : pending.future;
          },
        ),
      ),
    );
    await tester.pumpAndSettle();
    bool finished = false;
    final refresh = tester
        .widget<RefreshIndicator>(find.byType(RefreshIndicator))
        .onRefresh()
        .then((_) => finished = true);
    await tester.pump();
    expect(finished, isFalse);
    await tester.pumpWidget(const SizedBox.shrink());
    await refresh;
    expect(finished, isTrue);
    pending.complete(_page([2]));
    await tester.pumpAndSettle();
    expect(tester.takeException(), isNull);
  });

  testWidgets('pagination restarts at page one after pulling to refresh', (
    tester,
  ) async {
    final controller = PagifyController<int>();
    final pages = <int>[];
    await tester.pumpWidget(
      _app(
        _collection(
          controller: controller,
          load: (_, page) async {
            pages.add(page);
            return ([page], PaginationData(perPage: 1, totalPages: 2));
          },
        ),
      ),
    );
    await tester.pumpAndSettle();
    final scrollable = tester.state<ScrollableState>(
      find.byType(Scrollable).first,
    );
    scrollable.position.jumpTo(scrollable.position.maxScrollExtent);
    await tester.pumpAndSettle();
    expect(pages, [1, 2]);
    expect(controller.items, [1, 2]);
    final refresh = tester
        .widget<RefreshIndicator>(find.byType(RefreshIndicator))
        .onRefresh();
    await tester.pumpAndSettle();
    await refresh;
    expect(pages, [1, 2, 1]);
    expect(controller.items, [1]);
    expect(tester.takeException(), isNull);
  });
}

Widget _app(Widget child) => ScreenUtilInit(
  designSize: const Size(390, 844),
  builder: (_, __) => MaterialApp(home: Scaffold(body: child)),
);

AppPagify<int> _collection({
  required Future<(List<int>, PaginationData)> Function(BuildContext, int) load,
  PagifyController<int>? controller,
  Widget? header,
}) => AppPagify<int>(
  pagifyController: controller ?? PagifyController<int>(),
  enablePullRefresh: true,
  shrinkWrap: false,
  header: header,
  asyncCall: load,
  loadingBuilder: const Text('Loading'),
  emptyListView: const Center(
    child: SingleChildScrollView(child: Text('No items')),
  ),
  errorBuilder: (_) =>
      const Center(child: SingleChildScrollView(child: Text('Request failed'))),
  onError: (_, __, ___) {},
  itemBuilder: (_, __, ___, item) => SizedBox(
    height: controller == null ? 40 : 800,
    child: Text('Item $item'),
  ),
);

(List<int>, PaginationData) _page(List<int> items) =>
    (items, PaginationData(perPage: 20, totalPages: 1));

Future<void> _pull(WidgetTester tester) async {
  await tester.drag(find.byType(Scrollable).first, const Offset(0, 350));
  await tester.pump();
  await tester.pump(const Duration(seconds: 1));
}
