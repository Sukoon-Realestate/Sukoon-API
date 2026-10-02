import 'dart:convert';
import 'dart:io';

import 'package:easy_localization/easy_localization.dart';
import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:melos_core/config/language/languages.dart';
import 'package:melos_core/core/helpers/account_input_rules.dart';
import 'package:melos_core/core/helpers/validators.dart';
import 'package:sokoun_app/features/shared/auth/data/models/kyc_upload_documents_data.dart';
import 'package:sokoun_app/shared_widgets/email_field.dart';
import 'package:sokoun_app/shared_widgets/name_field.dart';
import 'package:sokoun_app/shared_widgets/password_field.dart';
import 'package:sokoun_app/shared_widgets/phone_field.dart';

void main() {
  TestWidgetsFlutterBinding.ensureInitialized();

  const MethodChannel preferencesChannel = MethodChannel(
    'plugins.flutter.io/shared_preferences',
  );

  setUpAll(() async {
    TestDefaultBinaryMessengerBinding.instance.defaultBinaryMessenger
        .setMockMethodCallHandler(preferencesChannel, (call) async {
          return call.method == 'getAll' ? <String, Object>{} : true;
        });
    await EasyLocalization.ensureInitialized();
  });

  tearDownAll(() {
    TestDefaultBinaryMessengerBinding.instance.defaultBinaryMessenger
        .setMockMethodCallHandler(preferencesChannel, null);
  });

  test('names support Arabic, Unicode letters, and ordinary separators', () {
    for (final String name in [
      'محمد أحمد',
      'مُحَمَّد',
      'Élodie',
      'Jose\u0301',
      "O'Connor",
      'Jean-Luc',
      '李',
      '  Ahmed  Ali  ',
      'A' * 50,
    ]) {
      expect(AccountInputRules.isValidName(name), isTrue, reason: name);
    }
    for (final String name in [
      '',
      '   ',
      '123',
      'Ahmed1',
      '<script>',
      'Ahmed@Ali',
      '-Ahmed',
      'Ahmed--Ali',
      'Ahmed\nAli',
      '😀',
      'A' * 51,
    ]) {
      expect(AccountInputRules.isValidName(name), isFalse, reason: name);
    }
  });

  test('email checks the entire address, labels, dots, and length limits', () {
    final String maximumEmail =
        '${'a' * 64}@${'b' * 63}.${'c' * 63}.${'d' * 61}';
    expect(maximumEmail.length, 254);
    for (final String email in [
      'user@example.com',
      '  USER+tag@sub.example-domain.co.uk  ',
      "o'connor@example.com",
      '${'a' * 60}@example.com',
      maximumEmail,
    ]) {
      expect(AccountInputRules.isValidEmail(email), isTrue, reason: email);
    }
    for (final String email in [
      '',
      'user@example.com<script>',
      'user@example.com trailing',
      'user@example.com@other.com',
      '.user@example.com',
      'user.@example.com',
      'user..name@example.com',
      'user name@example.com',
      'user@-example.com',
      'user@example-.com',
      'user@example..com',
      'user@example',
      'user@example.c',
      'user@${'a' * 64}.com',
      '${'a' * 65}@example.com',
      '${maximumEmail}e',
    ]) {
      expect(AccountInputRules.isValidEmail(email), isFalse, reason: email);
    }
  });

  test('Egyptian mobile rules preserve the leading zero and reject junk', () {
    for (final String prefix in ['010', '011', '012', '015']) {
      expect(
        AccountInputRules.isValidEgyptianMobile('  ${prefix}12345678  '),
        isTrue,
      );
    }
    for (final String phone in [
      '',
      '0101234567',
      '010123456789',
      '01312345678',
      '1012345678',
      '0101234abcd',
      '+201012345678',
      '010 12345678',
      '٠١٠١٢٣٤٥٦٧٨',
    ]) {
      expect(AccountInputRules.isValidEgyptianMobile(phone), isFalse);
    }
  });

  test('OTP is exactly six ASCII digits and keeps leading zeroes', () {
    expect(AccountInputRules.isValidOtpCode('001234'), isTrue);
    for (final String otp in [
      '',
      '1234',
      '12345',
      '1234567',
      'abcdef',
      '12345a',
      '123456\n',
      ' 123456',
      '١٢٣٤٥٦',
    ]) {
      expect(AccountInputRules.isValidOtpCode(otp), isFalse, reason: otp);
    }
  });

  test('registration password rejects whitespace and counts code points', () {
    expect(Validators.validatePassword('1234567'), isNotNull);
    expect(Validators.validatePassword('        '), isNotNull);
    expect(Validators.validatePassword('😀😀😀😀'), isNotNull);
    expect(Validators.validatePassword('😀😀😀😀😀😀😀😀'), isNull);
    expect(Validators.validatePassword('a<b>cdef'), isNull);
    expect(Validators.validatePassword('  secret  '), isNull);
  });

  test('login accepts existing passwords without creation constraints', () {
    expect(Validators.validateLoginPassword(null), isNotNull);
    expect(Validators.validateLoginPassword(''), isNotNull);
    expect(Validators.validateLoginPassword('short'), isNull);
    expect(Validators.validateLoginPassword('a<b>'), isNull);
    expect(Validators.validateLoginPassword('  secret  '), isNull);
  });

  test('confirmation compares the exact password, including spaces', () {
    expect(
      Validators.validatePasswordConfirmation('', password: 'password'),
      isNotNull,
    );
    expect(
      Validators.validatePasswordConfirmation(
        'password',
        password: ' password ',
      ),
      isNotNull,
    );
    expect(
      Validators.validatePasswordConfirmation(
        ' password ',
        password: ' password ',
      ),
      isNull,
    );
  });

  test('KYC readiness needs a numeric ID and actual uploads', () {
    final KycUploadDocumentsData body = KycUploadDocumentsData(
      nationalId: ' 29901011234567 ',
      frontIdImage: File('/tmp/front.jpg'),
      backIdImage: File('/tmp/back.jpg'),
      selfieImage: File('/tmp/selfie.jpg'),
    );
    expect(body.canSubmit, isTrue);
    expect(body.toJson()['national_id'], '29901011234567');
    expect(body.copyWith(nationalId: 'abcdefghijklmn').canSubmit, isFalse);
    expect(body.copyWith(nationalId: '299010112345678').canSubmit, isFalse);
    expect(
      const KycUploadDocumentsData(
        nationalId: '29901011234567',
        frontIdFileName: 'front.jpg',
        backIdFileName: 'back.jpg',
        selfieFileName: 'selfie.jpg',
      ).canSubmit,
      isFalse,
    );
    expect(const KycUploadDocumentsData().toJson(), isEmpty);
  });

  testWidgets(
    'shared fields show localized errors and accept corrected input',
    (tester) async {
      final GlobalKey<FormState> formKey = GlobalKey<FormState>();
      final TextEditingController name = TextEditingController(text: '123');
      final TextEditingController phone = TextEditingController(
        text: '01312345678',
      );
      final TextEditingController email = TextEditingController(
        text: 'user@example.com trailing',
      );
      addTearDown(name.dispose);
      addTearDown(phone.dispose);
      addTearDown(email.dispose);
      await tester.pumpWidget(
        _app(
          Form(
            key: formKey,
            child: Column(
              children: [
                SokoonNameField(controller: name),
                SokoonPhoneField(controller: phone),
                SokoonEmailField(controller: email),
              ],
            ),
          ),
        ),
      );
      await tester.pumpAndSettle();
      expect(formKey.currentState!.validate(), isFalse);
      await tester.pumpAndSettle();
      expect(find.textContaining('Enter a name of up to 50'), findsOneWidget);
      expect(find.textContaining('Enter an 11-digit Egyptian'), findsOneWidget);
      expect(
        find.textContaining('The email format should look'),
        findsOneWidget,
      );

      name.text = 'محمد أحمد';
      phone.text = '01012345678';
      email.text = 'user+tag@sub.example.com';
      await tester.pump();
      expect(formKey.currentState!.validate(), isTrue);
      await tester.pumpAndSettle();
      expect(find.textContaining('Enter an 11-digit Egyptian'), findsNothing);
      expect(tester.takeException(), isNull);
    },
  );

  testWidgets(
    'password field honors the login rule without changing its value',
    (tester) async {
      final GlobalKey<FormState> formKey = GlobalKey<FormState>();
      final TextEditingController password = TextEditingController(
        text: ' <a> ',
      );
      addTearDown(password.dispose);
      await tester.pumpWidget(
        _app(
          Form(
            key: formKey,
            child: SokoonPasswordField(
              controller: password,
              validator: Validators.validateLoginPassword,
            ),
          ),
        ),
      );
      await tester.pumpAndSettle();
      expect(formKey.currentState!.validate(), isTrue);
      expect(password.text, ' <a> ');
      expect(tester.takeException(), isNull);
    },
  );
}

Widget _app(Widget form) => EasyLocalization(
  supportedLocales: Languages.supportedLocales,
  path: Languages.translationsPath,
  assetLoader: const _AccountTranslationLoader(),
  startLocale: const Locale('en'),
  fallbackLocale: const Locale('en'),
  saveLocale: false,
  child: ScreenUtilInit(
    designSize: const Size(390, 844),
    builder: (context, _) => MaterialApp(
      localizationsDelegates: context.localizationDelegates,
      supportedLocales: context.supportedLocales,
      locale: context.locale,
      home: Scaffold(body: SingleChildScrollView(child: form)),
    ),
  ),
);

class _AccountTranslationLoader extends AssetLoader {
  const _AccountTranslationLoader();

  @override
  Future<Map<String, dynamic>> load(String path, Locale locale) async =>
      jsonDecode(
            File(
              '../../packages/core/assets/translations/${locale.languageCode}.json',
            ).readAsStringSync(),
          )
          as Map<String, dynamic>;
}
