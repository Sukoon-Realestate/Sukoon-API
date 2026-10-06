import 'package:flutter/services.dart';
import 'package:melos_core/core/helpers/validators.dart';

/// Accept Western, Arabic-Indic and Persian digits without moving the caret.
class LocalizedDigitsFormatter extends TextInputFormatter {
  const LocalizedDigitsFormatter({
    this.allowNegative = false,
    this.allowDecimal = false,
  });

  final bool allowNegative;
  final bool allowDecimal;

  @override
  TextEditingValue formatEditUpdate(
    TextEditingValue oldValue,
    TextEditingValue newValue,
  ) => Validators.formatLocalizedDigits(
    oldValue,
    newValue,
    allowNegative: allowNegative,
    allowDecimal: allowDecimal,
  );
}
