import 'dart:async';

import 'package:easy_localization/easy_localization.dart';
import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:flutter_bloc/flutter_bloc.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:melos_core/config/language/locale_keys.g.dart';
import 'package:melos_core/config/res/config_imports.dart';
import 'package:melos_core/core/base_crud/code/domain/base_domain_imports.dart';
import 'package:melos_core/core/base_crud/code/presentation/cubit/base_cubit/async_cubit.dart';
import 'package:melos_core/core/helpers/status_builder.dart';
import 'package:melos_core/core/widgets/exeption_view.dart';

void main() {
  TestWidgetsFlutterBinding.ensureInitialized();
  const preferencesChannel = MethodChannel(
    'plugins.flutter.io/shared_preferences',
  );
  late _StatusCubit cubit;

  setUpAll(() async {
    TestDefaultBinaryMessengerBinding.instance.defaultBinaryMessenger
        .setMockMethodCallHandler(preferencesChannel, (call) async {
          return call.method == 'getAll' ? <String, Object>{} : true;
        });
    await EasyLocalization.ensureInitialized();
  });

  setUp(() async {
    await injector.reset();
    injector.registerSingleton<BaseCrudUseCase>(_UnusedUseCase());
    cubit = _StatusCubit()..showSuccess();
  });

  tearDown(() async {
    await cubit.close();
    await injector.reset();
  });

  tearDownAll(() {
    TestDefaultBinaryMessengerBinding.instance.defaultBinaryMessenger
        .setMockMethodCallHandler(preferencesChannel, null);
  });

  testWidgets('loading more preserves the mounted scroll view and its offset', (
    tester,
  ) async {
    final controller = ScrollController();
    addTearDown(controller.dispose);
    await tester.pumpWidget(
      _screen(
        cubit: cubit,
        onRetry: () async {},
        builder: (data) => ListView(
          controller: controller,
          children: List.generate(
            30,
            (index) => SizedBox(height: 100, child: Text('$data $index')),
          ),
        ),
      ),
    );
    await tester.pumpAndSettle();
    controller.jumpTo(400);
    await tester.pump();
    final scrollable = tester.state(find.byType(Scrollable));

    cubit.setLoadingMore();
    await tester.pump();
    expect(tester.state(find.byType(Scrollable)), same(scrollable));
    expect(controller.offset, 400);

    cubit.showSuccess();
    await tester.pump();
    expect(tester.state(find.byType(Scrollable)), same(scrollable));
    expect(controller.offset, 400);
    expect(tester.takeException(), isNull);
    await tester.pumpWidget(const SizedBox.shrink());
  });

  for (final bool withShimmer in [false, true]) {
    testWidgets(
      'offline errors offer a working retry (shimmer: $withShimmer)',
      (tester) async {
        int retries = 0;
        await tester.pumpWidget(
          _screen(
            cubit: cubit,
            withShimmer: withShimmer,
            onRetry: () async {
              retries++;
              cubit.showSuccess();
            },
          ),
        );
        await tester.pumpAndSettle();

        cubit.setError(errorMessage: ' ${LocaleKeys.checkInternet} ');
        await tester.pump();
        await tester.pump();

        expect(find.byIcon(Icons.cloud_off_outlined), findsOneWidget);
        expect(find.byType(ExceptionView), findsNothing);
        expect(retries, 0);

        await tester.tap(find.text(LocaleKeys.ownerRetryAction));
        await tester.pumpAndSettle();

        expect(retries, 1);
        expect(find.text('Loaded content'), findsOneWidget);
        expect(find.byIcon(Icons.cloud_off_outlined), findsNothing);
        expect(tester.takeException(), isNull);
      },
    );
  }

  for (final String? message in ['Server unavailable', '', null]) {
    testWidgets('other errors show ExceptionView: $message', (tester) async {
      await tester.pumpWidget(_screen(cubit: cubit, onRetry: () async {}));
      await tester.pumpAndSettle();

      cubit.setError(errorMessage: message);
      await tester.pump();
      await tester.pump();

      expect(find.byType(ExceptionView), findsOneWidget);
      expect(find.byIcon(Icons.cloud_off_outlined), findsNothing);
      expect(find.text('Loaded content'), findsNothing);
      await tester.pumpWidget(const SizedBox.shrink());
    });
  }

  testWidgets('retry ignores repeated taps until the request completes', (
    tester,
  ) async {
    final request = Completer<void>();
    int retries = 0;
    await tester.pumpWidget(
      _screen(
        cubit: cubit,
        onRetry: () {
          retries++;
          return request.future;
        },
      ),
    );
    await tester.pumpAndSettle();
    cubit.setError(errorMessage: LocaleKeys.checkInternet);
    await tester.pump();
    await tester.pump();

    await tester.tap(find.text(LocaleKeys.ownerRetryAction));
    await tester.tap(find.text(LocaleKeys.ownerRetryAction));
    await tester.pump();

    expect(retries, 1);
    expect(find.byType(CircularProgressIndicator), findsOneWidget);
    expect(
      tester.widget<ElevatedButton>(find.byType(ElevatedButton)).onPressed,
      isNull,
    );

    request.complete();
    await tester.pumpAndSettle();

    expect(find.byType(CircularProgressIndicator), findsNothing);
    expect(find.text(LocaleKeys.ownerRetryAction), findsOneWidget);
    expect(tester.takeException(), isNull);
  });

  testWidgets('retry can finish after its view is disposed', (tester) async {
    final request = Completer<void>();
    await tester.pumpWidget(
      _screen(cubit: cubit, onRetry: () => request.future),
    );
    await tester.pumpAndSettle();
    cubit.setError(errorMessage: LocaleKeys.checkInternet);
    await tester.pump();
    await tester.pump();
    await tester.tap(find.text(LocaleKeys.ownerRetryAction));
    await tester.pump();

    await tester.pumpWidget(const SizedBox.shrink());
    request.complete();
    await tester.pump();

    expect(tester.takeException(), isNull);
  });
}

Widget _screen({
  required _StatusCubit cubit,
  required Future<void> Function() onRetry,
  bool withShimmer = true,
  Widget Function(String)? builder,
}) {
  final Future<void> initialRequest = Future<void>.value();
  return EasyLocalization(
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
        home: Scaffold(
          body: BlocProvider<_StatusCubit>.value(
            value: cubit,
            child: withShimmer
                ? StatusBuilder<_StatusCubit, String>.withShimmer(
                    initialDataForShimmer: '',
                    requestToTryAgainWhenError: initialRequest,
                    onRetry: onRetry,
                    builder: builder ?? (data) => Text(data),
                  )
                : StatusBuilder<_StatusCubit, String>(
                    requestToTryAgainWhenError: initialRequest,
                    onRetry: onRetry,
                    builder: builder ?? (data) => Text(data),
                  ),
          ),
        ),
      ),
    ),
  );
}

class _StatusCubit extends AsyncCubit<String> {
  _StatusCubit() : super('');

  void showSuccess() => emit(state.success(data: 'Loaded content'));
}

class _UnusedUseCase implements BaseCrudUseCase {
  @override
  dynamic noSuchMethod(Invocation invocation) => super.noSuchMethod(invocation);
}

class _Translations extends AssetLoader {
  const _Translations();

  @override
  Future<Map<String, dynamic>> load(String path, Locale locale) async => {
    'check_internet': 'Please check your internet connection',
    'exception_error': 'Connection unavailable',
    'owner_retry_action': 'Retry',
  };
}
