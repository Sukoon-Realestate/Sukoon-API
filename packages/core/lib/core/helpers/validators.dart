import 'package:easy_localization/easy_localization.dart';
import '../../config/language/locale_keys.g.dart';
import '../extensions/object.dart';
import '../navigation/navigator.dart';

class Validators {
  static String? validateChatMessage(String? value, {String? fieldTitle}) {
    final regex = RegExp(r'^[a-zA-Z\u0600-\u06FF\s]+$');
    final emptyRegex = RegExp(r'^(?!\s*$).+');
    if (value!.isEmpty) {
      return null;
    }

    if (!emptyRegex.hasMatch(value)) {
      return LocaleKeys.fillField;
    }

    if (value.isNull || !regex.hasMatch(value)) {
      return LocaleKeys.onlyLettersAllowed;
    }

    return null;
  }

  static String? validateEmpty(String? value, {String? fieldTitle}) {
    if (value == null || value.trim().isEmpty) {
      return fieldTitle == null
          ? LocaleKeys.fillField.tr(context: Go.context)
          : '${LocaleKeys.filedValidation.tr()} $fieldTitle';
    } else if (RegExp(r'[<>]').hasMatch(value)) {
      return LocaleKeys.scripInjectionValidate.tr(context: Go.context);
    }

    return null;
  }

  static String? validateName(String? value, {String? fieldTitle}) {
    if (value == null || value.trim().isEmpty) {
      return fieldTitle == null
          ? LocaleKeys.fillField.tr(context: Go.context)
          : '${LocaleKeys.filedValidation.tr()} $fieldTitle';
    } else if (value.length > 50) {
      return fieldTitle != null
          ? '$fieldTitle ${LocaleKeys.filedValidation.tr()}'
          : LocaleKeys.filedValidation.tr();
    }
    return null;
  }

  static String? validateIdentityNumber(String? value, {String? fieldTitle}) {
    if (value == null || value.trim().isEmpty) {
      return fieldTitle == null
          ? LocaleKeys.fillField.tr(context: Go.context)
          : '${LocaleKeys.filedValidation.tr()} $fieldTitle';
    } else if (value.length < 10 || value.length > 255) {
      return LocaleKeys.filedValidation.tr();
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
        return fieldTitle == null
            ? LocaleKeys.fillField.tr(context: Go.context)
            : '${LocaleKeys.filedValidation.tr()} $fieldTitle';
      }
      return null;
    } else if (num.tryParse(value) == null) {
      return LocaleKeys.theAgeMustBeANumber.tr(context: Go.context);
    } else {
      final age = num.parse(value);
      if (age < 18 || age > 150) {
        return LocaleKeys.theAgeMustBeAtLeast18YearsOld.tr(
          context: Go.context,
        ); // Or generic invalid range
      }
    }

    return null;
  }

  static String? validateOtpCode(String? value, {String? fieldTitle}) {
    if (value == null || value.isEmpty) {
      return fieldTitle == null
          ? LocaleKeys.fillField.tr(context: Go.context)
          : '${LocaleKeys.filedValidation.tr()} $fieldTitle';
    } else if (value.length < 4) {
      return LocaleKeys.theVerificationCodeMustConsistOf4Digits.tr(
        context: Go.context,
      );
    }

    return null;
  }

  static String? validateDowry({required String min, required String max}) {
    final num minNum = num.tryParse(min) ?? 0;
    final num maxNum = num.tryParse(max) ?? 0;

    if (minNum >= maxNum) {
      return LocaleKeys.theMinDowryCanNotBeGreaterThanMax.tr();
    }

    return null;
  }

  static String? validateEmail(String? value, {String? fieldTitle}) {
    if (value?.trim().isEmpty ?? true) {
      return fieldTitle == null
          ? LocaleKeys.fillField.tr(context: Go.context)
          : '${LocaleKeys.filedValidation.tr()} $fieldTitle';
    } else if (RegExp(r'[<>]').hasMatch(value!)) {
      return LocaleKeys.scripInjectionValidate.tr(context: Go.context);
    } else if (!RegExp(
      r"^[a-zA-Z0-9.a-zA-Z0-9.!#$%&'*+-/=?^_`{|}~]+@[a-zA-Z0-9]+\.["
      r'a-zA-Z]+',
    ).hasMatch(value)) {
      return LocaleKeys.mailValidation.tr(context: Go.context);
    } else if (value.length > 50) {
      return LocaleKeys.mailValidation.tr(context: Go.context);
    }
    return null;
  }

  static String? validatePhone(String? value, {String? message}) {
    if (value?.trim().isEmpty ?? true) {
      return message ?? LocaleKeys.fillField;
    } else if (!value!.startsWith('5')) {
      return LocaleKeys.thePhoneMustStartsWith5;
    } else if (value.length != 9) {
      return LocaleKeys.phoneShouldBe9Digits;
    } else if (!RegExp(
          r'^(5)(5|0|3|6|4|9|1|8|7)([0-9]{7})$',
        ).hasMatch(value.trim()) ||
        value.length < 9) {
      return message ?? LocaleKeys.phoneValidation.tr();
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
        return fieldTitle == null
            ? LocaleKeys.fillField.tr(context: Go.context)
            : '${LocaleKeys.filedValidation.tr()} $fieldTitle';
      }
      return null;
    }
    final numValue = int.tryParse(value);
    if (numValue == null) {
      return LocaleKeys.filedValidation.tr();
    }
    if (numValue < min || numValue > max) {
      return LocaleKeys.filedValidation.tr();
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
        return fieldTitle == null
            ? LocaleKeys.fillField.tr(context: Go.context)
            : '${LocaleKeys.filedValidation.tr()} $fieldTitle';
      }
      return null;
    }
    final numValue = num.tryParse(value);
    if (numValue == null) {
      return LocaleKeys.filedValidation.tr();
    }
    if (numValue < min || numValue > max) {
      return LocaleKeys.filedValidation.tr();
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
        return fieldTitle == null
            ? LocaleKeys.fillField.tr(context: Go.context)
            : '${LocaleKeys.filedValidation.tr()} $fieldTitle';
      }
      return null;
    }
    if (value.length < min || value.length > max) {
      return LocaleKeys.filedValidation.tr();
    }
    return null;
  }

  static String? noValidate(String value) {
    if (RegExp(r'[<>]').hasMatch(value)) {
      return LocaleKeys.scripInjectionValidate.tr(context: Go.context);
    } else {
      return null;
    }
  }

  // static String? validateDropDown<T>(T? value, {String? fieldTitle}) {
  //   if (value == null) {
  //     return fieldTitle != null ?
  //     '${LocaleKeys.please.tr()} $fieldTitle' :
  //     LocaleKeys.fillField.tr(context: Go.context);
  //   } else {
  //     return null;
  //   }
  // }
}
