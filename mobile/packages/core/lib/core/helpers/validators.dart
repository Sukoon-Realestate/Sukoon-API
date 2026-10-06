import 'dart:io';
import 'dart:ui' as ui;

import 'package:flutter/services.dart';
import '../../config/language/locale_keys.g.dart';

/// The single entry point for client input validation and normalization.
/// Uniqueness, credentials, OTP state, and Django password checks stay server-side.
class Validators {
  static const int nameMaxLength = 50;
  static const int fullNameMaxLength = 100;
  static const int emailMaxLength = 254;
  static const int emailLocalPartMaxLength = 64;
  static const int passwordMinLength = 8;
  static const int otpLength = 6;
  static const int nationalIdLength = 14;
  static const int accountImageMaxBytes = 10 * 1024 * 1024;
  static const int accountImageMaxMegabytes =
      accountImageMaxBytes ~/ (1024 * 1024);
  static const int chatMessageMaxLength = 5000;
  static const Duration propertyVideoMaxDuration = Duration(seconds: 60);
  static const Duration propertyVideoMinDuration = Duration(seconds: 1);
  static const int propertyMinPhotoCount = 10;
  static const int propertyMaxPhotoCount = 25;
  static final TextInputFormatter asciiDigitsOnly =
      FilteringTextInputFormatter.digitsOnly;

  static TextEditingValue formatLocalizedDigits(
    TextEditingValue oldValue,
    TextEditingValue newValue, {
    bool allowNegative = false,
    bool allowDecimal = false,
  }) {
    final TextEditingValue normalized = newValue.copyWith(
      text: String.fromCharCodes(
        newValue.text.runes.map((rune) {
          if (rune >= 0x0660 && rune <= 0x0669) return rune - 0x0660 + 0x30;
          if (rune >= 0x06f0 && rune <= 0x06f9) return rune - 0x06f0 + 0x30;
          if (allowDecimal && rune == 0x066b) return 0x2e;
          return rune;
        }),
      ),
    );
    if (allowNegative || allowDecimal) {
      final String sign = allowNegative ? '-?' : '';
      final String decimal = allowDecimal ? r'(\.[0-9]*)?' : '';
      return RegExp('^$sign[0-9]*$decimal\$').hasMatch(normalized.text)
          ? normalized
          : oldValue;
    }
    return asciiDigitsOnly.formatEditUpdate(oldValue, normalized);
  }

  static final RegExp _name = RegExp(r"^[\p{L}\p{M} '’\-]+$", unicode: true);
  static final RegExp _letter = RegExp(r'\p{L}', unicode: true);
  static final RegExp _emailLocalPart = RegExp(
    r"^[a-zA-Z0-9!#$%&'*+/=?^_`{|}~\-]+(?:\.[a-zA-Z0-9!#$%&'*+/=?^_`{|}~\-]+)*$",
  );
  // Quoted local parts and domain literals follow Django's EmailValidator:
  // https://github.com/django/django/blob/stable/5.2.x/django/core/validators.py
  static final RegExp _quotedEmailLocalPart = RegExp(
    r'^"([\x01-\x08\x0b\x0c\x0e-\x1f!#-\[\]-\x7f]|\\[\x01-\x09\x0b\x0c\x0e-\x7f])*"$',
  );
  static final RegExp _domainLabel = RegExp(
    r'^[a-zA-Z0-9\u00a1-\uffff](?:[a-zA-Z0-9\u00a1-\uffff\-]*[a-zA-Z0-9\u00a1-\uffff])?$',
    unicode: true,
  );

  static String normalizeEmail(String value) => value.trim().toLowerCase();
  static String normalizeOtpCode(String value) => value.trim();
  static String normalizeVisitTime(String value) =>
      RegExp(r'^[0-9]{2}:[0-9]{2}$').hasMatch(value) ? '$value:00' : value;
  static String normalizeEgyptianMobile(String value) =>
      value.trim().replaceAll(RegExp(r'[ ()\-]'), '');

  static bool isNonBlank(String? value) => value?.trim().isNotEmpty ?? false;
  static String? skipValidation<T>(T? value) => null;

  static String _message(String template, Map<String, Object> values) {
    return values.entries.fold(template, (message, entry) {
      final Object value = entry.value;
      final String text =
          value is num && value.isFinite && value == value.roundToDouble()
          ? '${value.toInt()}'
          : '$value';
      return message.replaceAll('{${entry.key}}', text);
    });
  }

  static String _requiredMessage({String? fieldTitle, String? fallback}) =>
      isNonBlank(fieldTitle)
      ? _message(LocaleKeys.validationFieldRequired, {'field': fieldTitle!})
      : fallback ?? LocaleKeys.fillField;

  static String _fieldMessage(String message, String? fieldTitle) =>
      isNonBlank(fieldTitle) ? '$fieldTitle: $message' : message;

  static String get accountDocumentUploadHint => _message(
    LocaleKeys.accountDocumentUploadHint,
    {'max': accountImageMaxMegabytes},
  );

  static String? validateRequired<T>(T? value, {String? message}) =>
      value == null || (value is String && value.trim().isEmpty)
      ? message ?? LocaleKeys.fillField
      : null;

  static bool isValidName(
    String value, {
    int maxLength = nameMaxLength,
    bool isRequired = true,
  }) {
    final String name = value.trim();
    if (name.isEmpty) return !isRequired;
    return name.runes.length <= maxLength &&
        _name.hasMatch(name) &&
        _letter.hasMatch(name);
  }

  static bool isValidEmail(String value) {
    final String email = value.trim();
    if (email.runes.length > emailMaxLength ||
        RegExp(r'[\r\n]').hasMatch(email)) {
      return false;
    }
    final int separator = email.lastIndexOf('@');
    if (separator < 1) return false;
    final String local = email.substring(0, separator);
    final String domain = email.substring(separator + 1);
    if (local.length > emailLocalPartMaxLength ||
        (!_emailLocalPart.hasMatch(local) &&
            !_quotedEmailLocalPart.hasMatch(local))) {
      return false;
    }
    if (domain == 'localhost') return true;
    if (domain.startsWith('[') && domain.endsWith(']')) {
      return InternetAddress.tryParse(domain.substring(1, domain.length - 1)) !=
          null;
    }
    final List<String> labels = domain.split('.');
    return labels.length >= 2 &&
        labels.every(
          (label) => label.runes.length <= 63 && _domainLabel.hasMatch(label),
        ) &&
        RegExp(
          r'^(?:[a-zA-Z\u00a1-\uffff\-]{2,63}|xn--[a-zA-Z0-9]{1,59})$',
          unicode: true,
        ).hasMatch(labels.last);
  }

  static bool isValidEgyptianMobile(String value, {bool isRequired = true}) {
    final String phone = normalizeEgyptianMobile(value);
    if (phone.isEmpty) return !isRequired;
    return RegExp(
      r'^(?:01[0125][0-9]{8}|\+201[0125][0-9]{8})$',
    ).hasMatch(phone);
  }

  static bool isValidOtpCode(String value) =>
      RegExp(r'^[0-9]{6}$').hasMatch(normalizeOtpCode(value));

  static bool isValidEgyptianNationalId(
    String value, {
    bool isRequired = true,
  }) => value.trim().isEmpty
      ? !isRequired
      : RegExp(r'^[0-9]{14}$').hasMatch(value.trim());

  static String? validateFullName(String? value) =>
      validateName(value, maxLength: fullNameMaxLength, isRequired: false);

  static String? validateGender(String? value, {bool isRequired = false}) {
    if (value == null || value.isEmpty) {
      return isRequired ? LocaleKeys.pleaseEnterTheGender : null;
    }
    return value == 'male' || value == 'female'
        ? null
        : LocaleKeys.accountGenderValidation;
  }

  static String? validateBirthDate(String? value, {bool isRequired = false}) {
    if (!isNonBlank(value)) {
      return isRequired ? LocaleKeys.accountBirthDateRequired : null;
    }
    final String date = value!.trim();
    if (!RegExp(r'^[0-9]{4}-[0-9]{2}-[0-9]{2}$').hasMatch(date)) {
      return LocaleKeys.accountBirthDateValidation;
    }
    final DateTime? parsed = DateTime.tryParse(date);
    return parsed != null &&
            parsed.year >= 1 &&
            parsed.toIso8601String().startsWith(date)
        ? null
        : LocaleKeys.accountBirthDateValidation;
  }

  static String? validateGoogleToken(String? value) =>
      isNonBlank(value) ? null : LocaleKeys.googleSignInFailed;

  static String? validateFilePresence(
    File? file, {
    bool isRequired = false,
    String? message,
  }) => file == null && isRequired
      ? message ?? LocaleKeys.validationFileRequired
      : null;

  /// Check size, actual format, and decodability, rather than the filename.
  /// The contract supplies no image dimension limit.
  static Future<String?> validateAccountImage(
    File? file, {
    bool allowGif = false,
    bool isRequired = false,
  }) async {
    final String? requiredError = validateFilePresence(
      file,
      isRequired: isRequired,
      message: LocaleKeys.validationImageRequired,
    );
    if (requiredError != null || file == null) return requiredError;
    try {
      final int size = await file.length();
      if (size > accountImageMaxBytes) {
        return _message(LocaleKeys.accountImageTooLarge, {
          'max': accountImageMaxMegabytes,
        });
      }
      if (size == 0) return LocaleKeys.accountImageInvalid;
      final Uint8List bytes = await file.readAsBytes();
      if (bytes.length > accountImageMaxBytes) {
        return _message(LocaleKeys.accountImageTooLarge, {
          'max': accountImageMaxMegabytes,
        });
      }
      final String? format = _imageFormat(bytes);
      if (format == null || (format == 'gif' && !allowGif)) {
        return allowGif
            ? LocaleKeys.accountAvatarFormatValidation
            : LocaleKeys.accountDocumentFormatValidation;
      }
      final ui.Codec codec = await ui.instantiateImageCodec(
        bytes,
        targetWidth: 1,
        targetHeight: 1,
      );
      try {
        final ui.FrameInfo frame = await codec.getNextFrame();
        frame.image.dispose();
      } finally {
        codec.dispose();
      }
      return null;
    } catch (_) {
      return LocaleKeys.accountImageInvalid;
    }
  }

  static Future<String?> validateKycDocuments({
    required String nationalId,
    File? frontIdImage,
    File? backIdImage,
    File? selfieImage,
  }) async {
    final String? idError = validateEgyptianNationalId(nationalId);
    if (idError != null) return idError;
    for (final ({String title, File? file}) document in [
      (title: LocaleKeys.idFrontLabel, file: frontIdImage),
      (title: LocaleKeys.idBackLabel, file: backIdImage),
      (title: LocaleKeys.selfiePhoto, file: selfieImage),
    ]) {
      final String? error = await validateAccountImage(document.file);
      if (error != null) return '${document.title}: $error';
    }
    return null;
  }

  static String? _imageFormat(Uint8List bytes) {
    bool startsWith(List<int> signature) =>
        bytes.length >= signature.length &&
        List.generate(
          signature.length,
          (index) => index,
        ).every((index) => bytes[index] == signature[index]);
    if (startsWith([0xff, 0xd8, 0xff])) return 'jpeg';
    if (startsWith([137, 80, 78, 71, 13, 10, 26, 10])) return 'png';
    if (startsWith([71, 73, 70, 56, 55, 97]) ||
        startsWith([71, 73, 70, 56, 57, 97])) {
      return 'gif';
    }
    if (startsWith([82, 73, 70, 70]) &&
        bytes.length >= 12 &&
        bytes[8] == 87 &&
        bytes[9] == 69 &&
        bytes[10] == 66 &&
        bytes[11] == 80) {
      return 'webp';
    }
    return null;
  }

  static bool isValidCoordinates({
    required double latitude,
    required double longitude,
  }) =>
      latitude.isFinite &&
      longitude.isFinite &&
      latitude >= -90 &&
      latitude <= 90 &&
      longitude >= -180 &&
      longitude <= 180;

  static bool isPositiveNumber(String value) {
    final num? parsed = num.tryParse(value.trim());
    return parsed != null && parsed.isFinite && parsed > 0;
  }

  static bool isValidPriceRange({required String min, required String max}) {
    final double? minimum = isNonBlank(min) ? double.tryParse(min) : null;
    final double? maximum = isNonBlank(max) ? double.tryParse(max) : null;
    if (isNonBlank(min) &&
        (minimum == null || !minimum.isFinite || minimum < 0)) {
      return false;
    }
    if (isNonBlank(max) &&
        (maximum == null || !maximum.isFinite || maximum < 0)) {
      return false;
    }
    return minimum == null || maximum == null || minimum <= maximum;
  }

  static bool isInteger(String value) => int.tryParse(value.trim()) != null;
  static bool isPositiveInteger(String value) =>
      isInteger(value) && int.parse(value.trim()) > 0;
  static bool hasMinimumLength(String value, int minimum) =>
      value.trim().length >= minimum;
  static bool isValidRating(int value) => value >= 1 && value <= 5;
  static bool isValidRatings(Iterable<int> values) =>
      values.every(isValidRating);
  static bool isValidChatContent(String value) =>
      isNonBlank(value) && value.trim().length <= chatMessageMaxLength;
  static String? validatePropertyVideoDuration(Duration value) =>
      value < propertyVideoMinDuration || value > propertyVideoMaxDuration
      ? _message(LocaleKeys.ownerPropertyVideoDurationInvalid, {
          'min': propertyVideoMinDuration.inSeconds,
          'max': propertyVideoMaxDuration.inSeconds,
        })
      : null;

  static bool isValidPropertyBasics({
    required Iterable<String> requiredFields,
    required Iterable<String> positiveNumbers,
    required String floor,
    required bool hasValidLocation,
  }) =>
      requiredFields.every(isNonBlank) &&
      positiveNumbers.every(isPositiveInteger) &&
      (floor.trim().isEmpty || isInteger(floor)) &&
      hasValidLocation;

  static bool isValidPropertyPhotos({required int count}) =>
      count >= propertyMinPhotoCount && count <= propertyMaxPhotoCount;

  static bool canAddPropertyPhoto(int count) => count < propertyMaxPhotoCount;
  static bool hasEnoughPropertyPhotos(int count) =>
      count >= propertyMinPhotoCount;

  static bool isValidPropertyPricing({
    required String monthlyPrice,
    required String rentalDuration,
    required String rentalUnit,
    required String suitableFor,
    required String description,
  }) =>
      isPositiveNumber(monthlyPrice) &&
      isPositiveInteger(rentalDuration) &&
      isNonBlank(rentalUnit) &&
      isNonBlank(suitableFor) &&
      hasMinimumLength(description, 10);

  static bool isValidVisitSelection({
    required int selectedDayIndex,
    required int dayCount,
    required Object? selectedTime,
  }) =>
      selectedDayIndex >= 0 &&
      selectedDayIndex < dayCount &&
      selectedTime != null;

  static String? validateChatMessage(String? value, {String? fieldTitle}) {
    final regex = RegExp(r'^[a-zA-Z\u0600-\u06FF\s]+$');
    final emptyRegex = RegExp(r'^(?!\s*$).+');
    if (value == null || value.isEmpty) {
      return null;
    }

    if (!emptyRegex.hasMatch(value)) {
      return _requiredMessage(
        fieldTitle: fieldTitle,
        fallback: LocaleKeys.chatMessageRequired,
      );
    }

    if (!regex.hasMatch(value)) {
      return _fieldMessage(LocaleKeys.chatMessageLettersValidation, fieldTitle);
    }

    return null;
  }

  static String? validateEmpty(String? value, {String? fieldTitle}) {
    if (value == null || value.trim().isEmpty) {
      return _requiredMessage(fieldTitle: fieldTitle);
    } else if (RegExp(r'[<>]').hasMatch(value)) {
      return _fieldMessage(LocaleKeys.scripInjectionValidate, fieldTitle);
    }

    return null;
  }

  static String? validateName(
    String? value, {
    String? fieldTitle,
    int maxLength = nameMaxLength,
    bool isRequired = true,
  }) {
    if (value == null || value.trim().isEmpty) {
      if (!isRequired) return null;
      return _requiredMessage(
        fieldTitle: fieldTitle,
        fallback: LocaleKeys.accountNameRequired,
      );
    } else if (value.trim().runes.length > maxLength) {
      return _fieldMessage(
        _message(LocaleKeys.accountNameTooLong, {'max': maxLength}),
        fieldTitle,
      );
    } else if (!isValidName(value, maxLength: maxLength)) {
      return _fieldMessage(LocaleKeys.accountNameValidation, fieldTitle);
    }
    return null;
  }

  static String? validateIdentityNumber(String? value, {String? fieldTitle}) {
    if (value == null || value.trim().isEmpty) {
      return _requiredMessage(
        fieldTitle: fieldTitle,
        fallback: LocaleKeys.validationIdentityRequired,
      );
    } else if (value.length < 10 || value.length > 255) {
      return _fieldMessage(
        _message(LocaleKeys.validationIdentityLength, {'min': 10, 'max': 255}),
        fieldTitle,
      );
    }
    return null;
  }

  static String? validateAge(
    String? value, {
    String? fieldTitle,
    bool isRequired = false,
  }) {
    if (value == null || value.isEmpty) {
      if (isRequired) {
        return _requiredMessage(fieldTitle: fieldTitle);
      }
      return null;
    } else if (num.tryParse(value) == null) {
      return _fieldMessage(LocaleKeys.theAgeMustBeANumber, fieldTitle);
    } else {
      final age = num.parse(value);
      if (age < 18 || age > 150) {
        return _fieldMessage(
          LocaleKeys.theAgeMustBeAtLeast18YearsOld,
          fieldTitle,
        );
      }
    }

    return null;
  }

  static String? validateOtpCode(String? value, {String? fieldTitle}) {
    if (value == null || value.trim().isEmpty) {
      return _requiredMessage(
        fieldTitle: fieldTitle,
        fallback: LocaleKeys.accountOtpRequired,
      );
    } else if (!isValidOtpCode(value)) {
      return _fieldMessage(
        _message(LocaleKeys.accountOtpValidation, {'length': otpLength}),
        fieldTitle,
      );
    }

    return null;
  }

  static String? validateDowry({required String min, required String max}) {
    final num minNum = num.tryParse(min) ?? 0;
    final num maxNum = num.tryParse(max) ?? 0;

    if (minNum >= maxNum) {
      return LocaleKeys.theMinDowryCanNotBeGreaterThanMax;
    }

    return null;
  }

  static String? validateEmail(String? value, {String? fieldTitle}) {
    if (value?.trim().isEmpty ?? true) {
      return _requiredMessage(
        fieldTitle: fieldTitle,
        fallback: LocaleKeys.accountEmailRequired,
      );
    }
    final String email = value!.trim();
    if (email.runes.length > emailMaxLength) {
      return _fieldMessage(
        _message(LocaleKeys.accountEmailTooLong, {'max': emailMaxLength}),
        fieldTitle,
      );
    }
    if (email.lastIndexOf('@') > emailLocalPartMaxLength) {
      return _fieldMessage(
        _message(LocaleKeys.accountEmailLocalPartTooLong, {
          'max': emailLocalPartMaxLength,
        }),
        fieldTitle,
      );
    }
    if (!isValidEmail(email)) {
      return _fieldMessage(LocaleKeys.mailValidation, fieldTitle);
    }
    return null;
  }

  static String? validatePassword(String? value) {
    if (value == null || value.isEmpty) {
      return LocaleKeys.passRequiredValidation;
    }

    if (value.trim().isEmpty) {
      return LocaleKeys.accountPasswordWhitespaceValidation;
    }

    if (value.runes.length < passwordMinLength) {
      return _message(LocaleKeys.accountPasswordTooShort, {
        'min': passwordMinLength,
      });
    }

    return null;
  }

  /// Login submits existing credentials exactly, without a creation policy.
  static String? validateLoginPassword(String? value) =>
      value == null || value.isEmpty ? LocaleKeys.passRequiredValidation : null;

  static String? validatePasswordConfirmation(
    String? value, {
    required String? password,
  }) {
    if (value == null || value.isEmpty) {
      return LocaleKeys.accountPasswordConfirmationRequired;
    }

    if (password != null && value != password) {
      return LocaleKeys.confirmValidation;
    }

    return validatePassword(value);
  }

  static String? validateEgyptianMobile(
    String? value, {
    bool isRequired = false,
  }) {
    if (value == null || value.trim().isEmpty) {
      return isRequired ? LocaleKeys.accountPhoneRequired : null;
    }
    return isValidEgyptianMobile(value)
        ? null
        : _message(LocaleKeys.accountEgyptianMobileValidation, {
            'internationalExample': '+201012345678',
          });
  }

  static String? validateEgyptianNationalId(
    String? value, {
    bool isRequired = false,
  }) {
    if (value == null || value.trim().isEmpty) {
      return isRequired ? LocaleKeys.accountNationalIdRequired : null;
    }
    return isValidEgyptianNationalId(value)
        ? null
        : _message(LocaleKeys.accountNationalIdValidation, {
            'length': nationalIdLength,
          });
  }

  static String? validatePhone(String? value, {String? message}) {
    if (value?.trim().isEmpty ?? true) {
      return message ?? LocaleKeys.accountPhoneRequired;
    } else if (!value!.startsWith('5')) {
      return LocaleKeys.thePhoneMustStartsWith5;
    } else if (value.length != 9) {
      return LocaleKeys.phoneShouldBe9Digits;
    } else if (!RegExp(
          r'^(5)(5|0|3|6|4|9|1|8|7)([0-9]{7})$',
        ).hasMatch(value.trim()) ||
        value.length < 9) {
      return message ?? LocaleKeys.phoneValidation;
    }

    return null;
  }

  static String? validateInteger(
    String? value, {
    String? fieldTitle,
    int min = 0,
    int max = 100,
    bool isRequired = true,
  }) {
    if (value == null || value.isEmpty) {
      if (isRequired) {
        return _requiredMessage(fieldTitle: fieldTitle);
      }
      return null;
    }
    final numValue = int.tryParse(value);
    if (numValue == null) {
      return _fieldMessage(LocaleKeys.validationInteger, fieldTitle);
    }
    if (numValue < min || numValue > max) {
      return _fieldMessage(
        _message(LocaleKeys.validationNumberRange, {'min': min, 'max': max}),
        fieldTitle,
      );
    }
    return null;
  }

  static String? validateNumeric(
    String? value, {
    String? fieldTitle,
    double min = 0,
    double max = 1000000,
    bool isRequired = true,
  }) {
    if (value == null || value.isEmpty) {
      if (isRequired) {
        return _requiredMessage(fieldTitle: fieldTitle);
      }
      return null;
    }
    final numValue = num.tryParse(value);
    if (numValue == null) {
      return _fieldMessage(LocaleKeys.validationNumber, fieldTitle);
    }
    if (numValue < min || numValue > max) {
      return _fieldMessage(
        _message(LocaleKeys.validationNumberRange, {'min': min, 'max': max}),
        fieldTitle,
      );
    }
    return null;
  }

  static String? validateString(
    String? value, {
    String? fieldTitle,
    int min = 0,
    int max = 255,
    bool isRequired = true,
  }) {
    if (value == null || value.isEmpty) {
      if (isRequired) {
        return _requiredMessage(fieldTitle: fieldTitle);
      }
      return null;
    }
    if (value.length < min) {
      return _fieldMessage(
        _message(LocaleKeys.validationMinLength, {'min': min}),
        fieldTitle,
      );
    }
    if (value.length > max) {
      return _fieldMessage(
        _message(LocaleKeys.validationMaxLength, {'max': max}),
        fieldTitle,
      );
    }
    return null;
  }

  static String? noValidate(String value) {
    if (RegExp(r'[<>]').hasMatch(value)) {
      return LocaleKeys.scripInjectionValidate;
    } else {
      return null;
    }
  }
}
