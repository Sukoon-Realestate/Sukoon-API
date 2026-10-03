import 'dart:convert';
import 'dart:io';

import 'package:easy_localization/easy_localization.dart';
import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:melos_core/config/language/languages.dart';
import 'package:melos_core/core/helpers/validators.dart';
import 'package:sokoun_app/features/shared/auth/data/models/kyc_upload_documents_data.dart';
import 'package:sokoun_app/features/shared/auth/data/models/register.dart';
import 'package:sokoun_app/features/shared/auth/data/models/otp.dart';
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
      '-Ahmed',
      'Ahmed--Ali',
      'A' * 50,
    ]) {
      expect(Validators.isValidName(name), isTrue, reason: name);
    }
    for (final String name in [
      '',
      '   ',
      '123',
      'Ahmed1',
      '<script>',
      'Ahmed@Ali',
      'Ahmed\nAli',
      '😀',
      'A' * 51,
    ]) {
      expect(Validators.isValidName(name), isFalse, reason: name);
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
      '"quoted@local"@example.com',
      'user@example.xn--p1ai',
      'user@例え.テスト',
      'user@[127.0.0.1]',
      '${'a' * 60}@example.com',
      maximumEmail,
    ]) {
      expect(Validators.isValidEmail(email), isTrue, reason: email);
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
      expect(Validators.isValidEmail(email), isFalse, reason: email);
    }
  });

  test(
    'Egyptian mobiles accept local, international, and formatted values',
    () {
      for (final String prefix in ['010', '011', '012', '015']) {
        expect(
          Validators.isValidEgyptianMobile('  ${prefix}12345678  '),
          isTrue,
        );
      }
      expect(Validators.isValidEgyptianMobile('+201012345678'), isTrue);
      expect(Validators.isValidEgyptianMobile('010 1234-5678'), isTrue);
      expect(Validators.isValidEgyptianMobile('+20 (10) 1234-5678'), isTrue);
      expect(Validators.validateEgyptianMobile(''), isNull);
      expect(Validators.validateEgyptianMobile(null), isNull);
      for (final String phone in [
        '',
        '0101234567',
        '010123456789',
        '01312345678',
        '1012345678',
        '0101234abcd',
        '+966512345678',
        '+2010123456789',
        '٠١٠١٢٣٤٥٦٧٨',
      ]) {
        expect(Validators.isValidEgyptianMobile(phone), isFalse);
      }
    },
  );

  test('OTP is exactly six ASCII digits and keeps leading zeroes', () {
    expect(Validators.isValidOtpCode('001234'), isTrue);
    expect(Validators.isValidOtpCode(' 001234\n'), isTrue);
    for (final String otp in [
      '',
      '1234',
      '12345',
      '1234567',
      'abcdef',
      '12345a',
      '١٢٣٤٥٦',
    ]) {
      expect(Validators.isValidOtpCode(otp), isFalse, reason: otp);
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

  test('profile rules allow empty fields and a 100-character full name', () {
    expect(Validators.validateFullName(null), isNull);
    expect(Validators.validateFullName(''), isNull);
    expect(Validators.validateFullName('A' * 100), isNull);
    expect(Validators.validateFullName('A' * 101), isNotNull);
    expect(Validators.validateName('A' * 51), isNotNull);
    expect(Validators.validateGender(null), isNull);
    expect(Validators.validateGender(''), isNull);
    expect(Validators.validateGender('male'), isNull);
    expect(Validators.validateGender('female'), isNull);
    expect(Validators.validateGender('invalid'), isNotNull);
    expect(Validators.validateEgyptianNationalId(null), isNull);
    expect(Validators.validateEgyptianNationalId('123'), isNotNull);
  });

  test(
    'optional birth date checks calendar dates without inventing age limits',
    () {
      expect(Validators.validateBirthDate(null), isNull);
      expect(Validators.validateBirthDate('2024-02-29'), isNull);
      expect(Validators.validateBirthDate('2025-02-29'), isNotNull);
      expect(Validators.validateBirthDate('2026-04-31'), isNotNull);
      expect(Validators.validateBirthDate('0000-01-01'), isNotNull);
      expect(Validators.validateBirthDate('2026-1-1'), isNotNull);
    },
  );

  test(
    'request normalization lowercases emails and preserves passwords and OTP zeroes',
    () {
      const RegisterBody body = RegisterBody(
        firstName: ' Ahmed ',
        lastName: ' Ali ',
        phone: '+20 (10) 1234-5678',
        email: ' USER+tag@Example.COM ',
        password: ' Exact password ',
        rePassword: ' Exact password ',
      );
      expect(body.toJson()['email'], 'user+tag@example.com');
      expect(body.toJson()['phone_number'], '+201012345678');
      expect(body.toJson()['first_name'], 'Ahmed');
      expect(body.toJson()['password'], ' Exact password ');
      expect(body.toJson()['re_password'], ' Exact password ');
      expect(
        const VerifyOtpBody(
          email: ' USER@Example.COM ',
          otp: ' 001234 ',
        ).toJson(),
        {'email': 'user@example.com', 'otp': '001234'},
      );
    },
  );

  test(
    'image validation checks actual bytes, size and optional uploads',
    () async {
      final Directory directory = await Directory.systemTemp.createTemp(
        'account_images_',
      );
      addTearDown(() => directory.delete(recursive: true));
      expect(await Validators.validateAccountImage(null), isNull);
      expect(
        await Validators.validateAccountImage(null, isRequired: true),
        isNotNull,
      );

      final List<int> pngBytes = File(
        '../../packages/core/assets/png/logo.png',
      ).readAsBytesSync();
      final File valid = await File(
        '${directory.path}/image.txt',
      ).writeAsBytes(pngBytes);
      expect(await Validators.validateAccountImage(valid), isNull);
      final File invalid = await File(
        '${directory.path}/image.png',
      ).writeAsString('not an image');
      expect(await Validators.validateAccountImage(invalid), isNotNull);
      final File corrupt = await File(
        '${directory.path}/corrupt.png',
      ).writeAsBytes([137, 80, 78, 71, 13, 10, 26, 10, 0]);
      expect(await Validators.validateAccountImage(corrupt), isNotNull);

      final File boundary = await File(
        '${directory.path}/boundary.png',
      ).writeAsBytes(pngBytes);
      final RandomAccessFile boundaryHandle = await boundary.open(
        mode: FileMode.append,
      );
      await boundaryHandle.truncate(Validators.accountImageMaxBytes);
      await boundaryHandle.close();
      expect(await Validators.validateAccountImage(boundary), isNull);
      final RandomAccessFile oversizedHandle = await boundary.open(
        mode: FileMode.append,
      );
      await oversizedHandle.truncate(Validators.accountImageMaxBytes + 1);
      await oversizedHandle.close();
      expect(await Validators.validateAccountImage(boundary), isNotNull);

      final File gif = await File('${directory.path}/avatar.gif').writeAsBytes(
        base64Decode(
          'R0lGODlhAQABAIAAAAAAAP///yH5BAEAAAAALAAAAAABAAEAAAIBRAA7',
        ),
      );
      expect(
        await Validators.validateAccountImage(gif, allowGif: true),
        isNull,
      );
      expect(await Validators.validateAccountImage(gif), isNotNull);
      expect(await Validators.validateKycDocuments(nationalId: ''), isNull);
      expect(
        await Validators.validateKycDocuments(nationalId: '123'),
        isNotNull,
      );
      expect(
        await Validators.validateKycDocuments(nationalId: '', selfieImage: gif),
        isNotNull,
      );
    },
  );

  test(
    'other app input policies use centralized finite, rating and duration checks',
    () {
      expect(Validators.isPositiveNumber('Infinity'), isFalse);
      expect(Validators.isPositiveNumber('NaN'), isFalse);
      expect(Validators.isPositiveNumber('12.5'), isTrue);
      expect(
        Validators.isValidCoordinates(latitude: double.nan, longitude: 31),
        isFalse,
      );
      expect(Validators.isValidRatings([1, 5, 3]), isTrue);
      expect(Validators.isValidRatings([1, 6, 3]), isFalse);
      expect(Validators.isValidChatContent(' '), isFalse);
      expect(Validators.isValidChatContent('a' * 5000), isTrue);
      expect(Validators.isValidChatContent('a' * 5001), isFalse);
      expect(
        Validators.validatePropertyVideoDuration(const Duration(seconds: 60)),
        isNull,
      );
      expect(
        Validators.validatePropertyVideoDuration(
          const Duration(milliseconds: 60001),
        ),
        isNotNull,
      );
      expect(
        Validators.isValidVisitSelection(
          selectedDayIndex: -1,
          dayCount: 2,
          selectedTime: Object(),
        ),
        isFalse,
      );
    },
  );

  test('KYC permits partial updates while validating any supplied ID', () {
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
      isTrue,
    );
    expect(const KycUploadDocumentsData().canSubmit, isTrue);
    expect(const KycUploadDocumentsData().toJson(), isEmpty);
  });

  for (final String language in ['en', 'ar']) {
    testWidgets('phone field adds the Egyptian country code in $language', (
      tester,
    ) async {
      final TextEditingController phone = TextEditingController();
      final List<String?> changes = [];
      addTearDown(phone.dispose);
      await tester.pumpWidget(
        _app(
          SokoonPhoneField(controller: phone, onChanged: changes.add),
          languageCode: language,
        ),
      );
      await tester.pumpAndSettle();
      expect(phone.text, isEmpty);
      final field = find.byType(TextFormField);

      for (final String input in [
        '01012345678',
        '1012345678',
        '+201012345678',
      ]) {
        await tester.enterText(field, input);
        await tester.pump();
        expect(phone.text, '+201012345678');
        expect(phone.selection, const TextSelection.collapsed(offset: 13));
        expect(changes.last, phone.text);
        expect(Validators.isValidEgyptianMobile(phone.text), isTrue);
      }

      await tester.enterText(field, '0');
      for (final String digit in '1012345678'.split('')) {
        tester.testTextInput.enterText('${phone.text}$digit');
        await tester.pump();
      }
      expect(phone.text, '+201012345678');

      await tester.enterText(field, '');
      expect(phone.text, isEmpty);
      expect(changes.last, isEmpty);
      for (final String text in ['+', '+2', '+20', '+201012345678']) {
        tester.testTextInput.enterText(text);
        await tester.pump();
        expect(phone.text, text);
      }
      expect(tester.takeException(), isNull);
    });

    testWidgets(
      'shared fields show localized errors and accept corrected input in $language',
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
            languageCode: language,
          ),
        );
        await tester.pumpAndSettle();
        expect(formKey.currentState!.validate(), isFalse);
        await tester.pumpAndSettle();
        expect(
          find.textContaining(
            language == 'en'
                ? 'Use letters, spaces'
                : 'استخدم الحروف والمسافات',
          ),
          findsOneWidget,
        );
        expect(
          find.textContaining(
            language == 'en'
                ? 'Enter a valid Egyptian mobile'
                : 'أدخل رقم موبايل مصريًا صحيحًا',
          ),
          findsOneWidget,
        );
        expect(
          find.textContaining(
            language == 'en'
                ? 'Enter a valid email address'
                : 'أدخل بريدًا إلكترونيًا صحيحًا',
          ),
          findsOneWidget,
        );

        name.text = 'A' * 51;
        email.text = '${'a' * 65}@example.com';
        expect(formKey.currentState!.validate(), isFalse);
        await tester.pumpAndSettle();
        expect(
          find.text(
            language == 'en'
                ? 'Name must contain 50 characters or fewer'
                : 'يجب ألا يزيد الاسم عن 50 حرفًا',
          ),
          findsOneWidget,
        );
        expect(
          find.textContaining(
            language == 'en'
                ? '64 characters or fewer before the at sign'
                : 'يسبق @ في البريد الإلكتروني عن 64',
          ),
          findsOneWidget,
        );

        name.clear();
        email.clear();
        expect(formKey.currentState!.validate(), isFalse);
        await tester.pumpAndSettle();
        expect(
          find.text(language == 'en' ? 'Enter your name' : 'أدخل اسمك'),
          findsOneWidget,
        );
        expect(
          find.text(
            language == 'en'
                ? 'Enter your email address'
                : 'أدخل بريدك الإلكتروني',
          ),
          findsOneWidget,
        );

        name.text = 'محمد أحمد';
        await tester.enterText(
          find.descendant(
            of: find.byType(SokoonPhoneField),
            matching: find.byType(TextFormField),
          ),
          '+201012345678',
        );
        expect(phone.text, '+201012345678');
        email.text = 'user+tag@sub.example.com';
        await tester.pump();
        expect(formKey.currentState!.validate(), isTrue);
        await tester.pumpAndSettle();
        expect(
          find.textContaining(
            language == 'en'
                ? 'Enter a valid Egyptian mobile'
                : 'أدخل رقم موبايل مصريًا صحيحًا',
          ),
          findsNothing,
        );
        expect(tester.takeException(), isNull);
      },
    );
  }

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

Widget _app(Widget form, {String languageCode = 'en'}) => EasyLocalization(
  supportedLocales: Languages.supportedLocales,
  path: Languages.translationsPath,
  assetLoader: const _AccountTranslationLoader(),
  startLocale: Locale(languageCode),
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
