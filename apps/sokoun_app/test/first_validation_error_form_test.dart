import 'dart:async';
import 'dart:convert';
import 'dart:io';

import 'package:easy_localization/easy_localization.dart';
import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:melos_core/config/language/locale_keys.g.dart';
import 'package:melos_core/config/res/config_imports.dart';
import 'package:melos_core/core/base_crud/code/domain/base_domain_imports.dart';
import 'package:melos_core/core/base_crud/code/domain/usecases/pagination_response.dart';
import 'package:melos_core/core/error/failure.dart';
import 'package:melos_core/core/navigation/navigator.dart';
import 'package:melos_core/core/widgets/buttons/app_loading_button.dart';
import 'package:melos_core/core/widgets/first_validation_error_form.dart';
import 'package:multiple_result/multiple_result.dart';
import 'package:sokoun_app/features/main_view/data/enums/app_workspace.dart';
import 'package:sokoun_app/features/shared/auth/presentation/screens/login_screen.dart';
import 'package:sokoun_app/features/shared/auth/presentation/screens/otp_screen.dart';
import 'package:sokoun_app/features/shared/auth/presentation/widgets/forgot_password/forgot_password_form.dart';
import 'package:sokoun_app/features/shared/profile/imports.dart'
    show ChangePasswordScreen;
import 'package:sokoun_app/features/shared/chat/presentation/widgets/chat_thread/chat_composer.dart';
import 'package:sokoun_app/features/shared/support/imports.dart'
    show SupportNewTicketScreen;
import 'package:sokoun_app/features/tenant/visits/imports.dart';
import 'package:sokoun_app/shared_widgets/sokoun_theme.dart';
import 'package:sokoun_app/shared_widgets/sokoun_validation_field.dart';
import 'package:toastification/toastification.dart';

void main() {
  TestWidgetsFlutterBinding.ensureInitialized();
  late _Repository repository;

  setUpAll(() async {
    TestDefaultBinaryMessengerBinding.instance.defaultBinaryMessenger
        .setMockMethodCallHandler(
          const MethodChannel('plugins.flutter.io/shared_preferences'),
          (call) async => call.method == 'getAll' ? <String, Object>{} : true,
        );
    await EasyLocalization.ensureInitialized();
  });

  setUp(() async {
    toastification.managers.clear();
    await injector.reset();
    repository = _Repository();
    injector.registerSingleton<BaseCrudUseCase>(
      BaseCrudUseCase(repository: repository),
    );
  });

  tearDown(() async {
    toastification.dismissAll(delayForAnimation: false);
    await injector.reset();
  });

  tearDownAll(() {
    TestDefaultBinaryMessengerBinding.instance.defaultBinaryMessenger
        .setMockMethodCallHandler(
          const MethodChannel('plugins.flutter.io/shared_preferences'),
          null,
        );
  });

  testWidgets('chat send keeps the keyboard open and outside taps dismiss it', (
    tester,
  ) async {
    final controller = TextEditingController();
    addTearDown(controller.dispose);
    int submissions = 0;
    await _mount(
      tester,
      Scaffold(
        body: Column(
          children: [
            TextButton(onPressed: () {}, child: const Text('Outside composer')),
            ChatComposer(
              controller: controller,
              onSendPressed: () {
                submissions++;
                controller.clear();
              },
            ),
          ],
        ),
      ),
    );
    await tester.enterText(find.byType(TextField), 'Message');
    await tester.pump();
    final focus = tester
        .widget<EditableText>(find.byType(EditableText))
        .focusNode;
    expect(focus.hasFocus, isTrue);
    await tester.tap(find.byIcon(Icons.send_rounded));
    await tester.pump();
    expect(submissions, 1);
    expect(focus.hasFocus, isTrue);
    expect(controller.text, isEmpty);
    expect(
      tester.state<FormFieldState<String>>(find.byType(TextFormField)).hasError,
      isFalse,
    );
    await tester.enterText(find.byType(TextField), 'Another message');
    await tester.pump();
    await tester.testTextInput.receiveAction(TextInputAction.send);
    await tester.pump();
    expect(submissions, 2);
    expect(focus.hasFocus, isTrue);
    await tester.tap(find.text('Outside composer'));
    await tester.pump();
    expect(focus.hasFocus, isFalse);
    expect(tester.takeException(), isNull);
  });

  testWidgets(
    'reports one error in field order and scrolls after each correction',
    (tester) async {
      final first = TextEditingController();
      final second = TextEditingController();
      final scroll = ScrollController();
      addTearDown(first.dispose);
      addTearDown(second.dispose);
      addTearDown(scroll.dispose);
      final firstKey = GlobalKey();
      final secondKey = GlobalKey();
      final errors = <FirstValidationError>[];
      int submissions = 0;
      late Future<void> Function() submit;
      String? required(String? value) =>
          value?.isNotEmpty == true ? null : 'Required';

      await _mount(
        tester,
        Scaffold(
          body: FirstValidationErrorForm(
            showToast: false,
            validationFields: () => [
              FirstValidationErrorField(
                fieldKey: firstKey,
                title: 'First field',
                value: first.text,
                validator: required,
              ),
              FirstValidationErrorField(
                fieldKey: secondKey,
                title: 'Second field',
                value: second.text,
                validator: required,
              ),
            ],
            onValidationError: errors.add,
            onValid: () => submissions++,
            builder: (context, onSubmit) {
              submit = onSubmit;
              return SingleChildScrollView(
                controller: scroll,
                child: Column(
                  children: [
                    const SizedBox(height: 900),
                    TextFormField(
                      key: firstKey,
                      controller: first,
                      validator: required,
                    ),
                    const SizedBox(height: 800),
                    TextFormField(
                      key: secondKey,
                      controller: second,
                      validator: required,
                    ),
                    const SizedBox(height: 900),
                  ],
                ),
              );
            },
          ),
        ),
      );

      await submit();
      await tester.pumpAndSettle();
      expect(errors.single.field.fieldKey, firstKey);
      expect(scroll.offset, greaterThan(0));
      final firstOffset = scroll.offset;
      expect(submissions, 0);

      first.text = 'Corrected';
      await tester.pump();
      await submit();
      await tester.pumpAndSettle();
      expect(errors, hasLength(2));
      expect(errors.last.field.fieldKey, secondKey);
      expect(scroll.offset, greaterThan(firstOffset));
      expect(submissions, 0);

      second.text = 'Corrected';
      await tester.pump();
      await submit();
      expect(submissions, 1);
    },
  );

  testWidgets(
    'selection validation blocks submission without a native FormField',
    (tester) async {
      final selectionKey = GlobalKey();
      String selection = '';
      int submissions = 0;
      FirstValidationError? error;
      late Future<void> Function() submit;
      await _mount(
        tester,
        Scaffold(
          body: FirstValidationErrorForm(
            validationFields: () => [
              FirstValidationErrorField(
                fieldKey: selectionKey,
                title: 'Property type',
                value: selection,
                validator: (value) => value == '' ? 'Choose a type' : null,
              ),
            ],
            onValidationError: (value) => error = value,
            onValid: () => submissions++,
            builder: (context, onSubmit) {
              submit = onSubmit;
              return Text('Selection control', key: selectionKey);
            },
          ),
        ),
      );
      await submit();
      await tester.pump();
      await tester.pump();
      await tester.pump(const Duration(milliseconds: 400));
      expect(error?.field.fieldKey, selectionKey);
      expect(find.text('Property type'), findsOneWidget);
      expect(find.text('Choose a type'), findsOneWidget);
      expect(submissions, 0);
      selection = 'apartment';
      await submit();
      expect(submissions, 1);
      await _dismissToasts(tester);
    },
  );

  testWidgets(
    'awaits submission and blocks duplicate button and keyboard calls',
    (tester) async {
      final pending = Completer<void>();
      int submissions = 0;
      late Future<void> Function() submit;
      await _mount(
        tester,
        Scaffold(
          body: FirstValidationErrorForm(
            validationFields: () => const [],
            onValid: () {
              submissions++;
              return pending.future;
            },
            builder: (context, onSubmit) {
              submit = onSubmit;
              return AppLoadingButton(
                asyncCall: (_) => onSubmit(),
                title: 'Submit',
              );
            },
          ),
        ),
      );
      await tester.tap(find.byType(ElevatedButton));
      await tester.pump();
      expect(submissions, 1);
      expect(find.byType(CircularProgressIndicator), findsOneWidget);
      expect(
        tester.widget<ElevatedButton>(find.byType(ElevatedButton)).onPressed,
        isNull,
      );
      await submit();
      expect(submissions, 1);
      pending.complete();
      await tester.pumpAndSettle();
      expect(find.byType(CircularProgressIndicator), findsNothing);
      expect(
        tester.widget<ElevatedButton>(find.byType(ElevatedButton)).onPressed,
        isNotNull,
      );
    },
  );

  testWidgets(
    'failed submissions can retry and pending submissions can unmount',
    (tester) async {
      int submissions = 0;
      final pending = Completer<void>();
      late Future<void> Function() submit;
      await _mount(
        tester,
        Scaffold(
          body: FirstValidationErrorForm(
            validationFields: () => const [],
            onValid: () async {
              submissions++;
              if (submissions == 1) throw StateError('Request failed');
              await pending.future;
            },
            builder: (context, onSubmit) {
              submit = onSubmit;
              return const Text('Form');
            },
          ),
        ),
      );
      await expectLater(submit(), throwsStateError);
      final retry = submit();
      expect(submissions, 2);
      await tester.pumpWidget(const SizedBox.shrink());
      pending.complete();
      await retry;
      expect(tester.takeException(), isNull);
    },
  );

  testWidgets(
    'login reports email before password and never submits invalid input',
    (tester) async {
      await _mount(tester, const LoginScreen());
      final button = find.byType(AppLoadingButton);
      await tester.ensureVisible(button);
      await tester.tap(button);
      await tester.pump();
      await tester.pump();
      await tester.pump(const Duration(milliseconds: 400));
      expect(find.text(LocaleKeys.email), findsNWidgets(2));
      expect(find.text(LocaleKeys.password), findsOneWidget);
      expect(repository.calls, 0);
      await _dismissToasts(tester);
      await tester.enterText(
        find.byType(TextFormField).first,
        'user@example.com',
      );
      await tester.ensureVisible(button);
      await tester.tap(button);
      await tester.pump();
      await tester.pump();
      await tester.pump(const Duration(milliseconds: 400));
      expect(find.text(LocaleKeys.password), findsNWidgets(2));
      expect(repository.calls, 0);
      await _dismissToasts(tester);
    },
  );

  testWidgets(
    'OTP reports incomplete codes instead of silently ignoring confirm',
    (tester) async {
      bool verified = false;
      await _mount(
        tester,
        OtpScreen(email: 'user@example.com', onVerified: () => verified = true),
      );
      await tester.enterText(find.byType(EditableText), '123');
      await tester.ensureVisible(find.byType(AppLoadingButton));
      await tester.tap(find.byType(AppLoadingButton));
      await tester.pump();
      await tester.pump();
      await tester.pump(const Duration(milliseconds: 400));
      expect(find.text(LocaleKeys.verificationCode), findsNWidgets(2));
      expect(repository.calls, 0);
      expect(verified, isFalse);
      await _dismissToasts(tester);
      await tester.pumpWidget(const SizedBox.shrink());
    },
  );

  for (final flow in [
    (
      name: 'password change',
      screen: const ChangePasswordScreen(),
      firstTitle: () => LocaleKeys.settingsCurrentPassword,
      secondTitle: () => LocaleKeys.createNewPassword,
      correction: 'existing-password',
    ),
    (
      name: 'support ticket',
      screen: const SupportNewTicketScreen(workspace: AppWorkspace.tenant),
      firstTitle: () => LocaleKeys.supportSubject,
      secondTitle: () => LocaleKeys.supportDetails,
      correction: 'A valid ticket subject',
    ),
  ]) {
    testWidgets(
      '${flow.name} reports its first invalid field before the next',
      (tester) async {
        await _mount(tester, flow.screen);
        final button = find.byType(AppLoadingButton);
        await tester.tap(button);
        await tester.pump();
        await tester.pump();
        await tester.pump(const Duration(milliseconds: 400));
        expect(find.text(flow.firstTitle()), findsNWidgets(2));
        expect(find.text(flow.secondTitle()), findsOneWidget);
        expect(repository.calls, 0);
        await _dismissToasts(tester);

        await tester.enterText(
          find.byType(TextFormField).first,
          flow.correction,
        );
        await tester.tap(button);
        await tester.pump();
        await tester.pump();
        await tester.pump(const Duration(milliseconds: 400));
        expect(find.text(flow.secondTitle()), findsNWidgets(2));
        expect(repository.calls, 0);
        await _dismissToasts(tester);
      },
    );
  }

  testWidgets(
    'password reset keyboard submit shares validation and duplicate guard',
    (tester) async {
      final email = TextEditingController();
      addTearDown(email.dispose);
      final pending = Completer<void>();
      int submissions = 0;
      await _mount(
        tester,
        Scaffold(
          body: SingleChildScrollView(
            child: ForgotPasswordForm(
              emailController: email,
              hasSubmittedInvalidEmail: false,
              isEmailValid: false,
              onEmailChanged: () {},
              onBackToLogin: () {},
              onSubmit: (_) {
                submissions++;
                return pending.future;
              },
            ),
          ),
        ),
      );
      await tester.enterText(find.byType(TextFormField), 'invalid');
      await tester.testTextInput.receiveAction(TextInputAction.done);
      await tester.pump();
      expect(submissions, 0);
      await _dismissToasts(tester);
      await tester.enterText(find.byType(TextFormField), 'user@example.com');
      await tester.testTextInput.receiveAction(TextInputAction.done);
      await tester.pump();
      expect(submissions, 1);
      await tester.tap(find.byType(AppLoadingButton));
      await tester.pump();
      expect(submissions, 1);
      pending.complete();
      await tester.pumpAndSettle();
    },
  );

  testWidgets(
    'booking reports missing time and accepts the corrected selection',
    (tester) async {
      final note = TextEditingController();
      final time = ValueNotifier<TimeOfDay?>(null);
      addTearDown(note.dispose);
      addTearDown(time.dispose);
      int submissions = 0;
      await _mount(
        tester,
        Scaffold(
          body: ValueListenableBuilder<TimeOfDay?>(
            valueListenable: time,
            builder: (context, selectedTime, _) => BookVisitForm(
              property: VisitPropertyContent.initial(),
              days: const [
                VisitDayContent(
                  weekday: 'Monday',
                  day: '5',
                  month: '10',
                  visitDate: '2026-10-05',
                ),
              ],
              selectedDayIndex: 0,
              selectedTime: selectedTime,
              noteController: note,
              onDaySelected: (_) {},
              onTimeSelected: (value) => time.value = value,
              onConfirmPressed: (_) async => submissions++,
            ),
          ),
        ),
      );
      final button = find.byType(AppLoadingButton);
      await tester.ensureVisible(button);
      await tester.tap(button);
      await tester.pump();
      await tester.pump();
      await tester.pump(const Duration(milliseconds: 400));
      expect(find.text(LocaleKeys.tenantVisitChooseTime), findsNWidgets(3));
      expect(submissions, 0);
      await _dismissToasts(tester);
      time.value = const TimeOfDay(hour: 14, minute: 0);
      await tester.pump();
      final timeField = find.descendant(
        of: find.byType(SokounValidationField).last,
        matching: find.byType(FormField<String>),
      );
      expect(
        find.descendant(
          of: timeField,
          matching: find.text(LocaleKeys.fillField),
        ),
        findsNothing,
      );
      await tester.ensureVisible(button);
      await tester.tap(button);
      await tester.pumpAndSettle();
      expect(submissions, 1);
      expect(tester.takeException(), isNull);
    },
  );
}

Future<void> _dismissToasts(WidgetTester tester) async {
  toastification.dismissAll(delayForAnimation: false);
  await tester.pump();
  await tester.pump(const Duration(milliseconds: 400));
}

Future<void> _mount(WidgetTester tester, Widget screen) async {
  tester.view.physicalSize = const Size(390, 844);
  tester.view.devicePixelRatio = 1;
  addTearDown(tester.view.reset);
  await tester.pumpWidget(
    EasyLocalization(
      supportedLocales: const [Locale('ar'), Locale('en')],
      path: 'unused',
      assetLoader: const _Translations(),
      startLocale: const Locale('en'),
      saveLocale: false,
      child: ScreenUtilInit(
        designSize: const Size(360, 690),
        enableScaleWH: () => false,
        enableScaleText: () => false,
        builder: (context, _) => MaterialApp(
          navigatorKey: Go.navigatorKey,
          theme: SokounTheme.light,
          locale: context.locale,
          localizationsDelegates: context.localizationDelegates,
          supportedLocales: context.supportedLocales,
          home: screen,
        ),
      ),
    ),
  );
  await tester.pumpAndSettle();
}

class _Translations extends AssetLoader {
  const _Translations();

  @override
  Future<Map<String, dynamic>> load(String path, Locale locale) async =>
      jsonDecode(
            File(
              '../../packages/core/assets/translations/${locale.languageCode}.json',
            ).readAsStringSync(),
          )
          as Map<String, dynamic>;
}

class _Repository implements BaseRepository {
  int calls = 0;

  @override
  Future<Result<BaseModel<T>, Failure>> crudCall<T>(
    CrudBaseParmas<T> params,
  ) async {
    calls++;
    return const Error(Failure('Unexpected submission'));
  }

  @override
  Future<Result<List<T>, Failure>> getBaseIdAndNameEntity<T extends BaseEntity>(
    GetBaseEntityParams? param,
  ) => throw UnimplementedError();
}
