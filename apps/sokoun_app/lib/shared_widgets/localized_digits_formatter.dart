import 'package:flutter/services.dart';

/// Accept Western, Arabic-Indic and Persian digits without moving the caret.
class LocalizedDigitsFormatter extends TextInputFormatter {
  const LocalizedDigitsFormatter();

  @override
  TextEditingValue formatEditUpdate(
    TextEditingValue oldValue,
    TextEditingValue newValue,
  ) {
    final normalized = newValue.copyWith(
      text: String.fromCharCodes(
        newValue.text.runes.map((rune) {
          if (rune >= 0x0660 && rune <= 0x0669) return rune - 0x0660 + 0x30;
          if (rune >= 0x06f0 && rune <= 0x06f9) return rune - 0x06f0 + 0x30;
          return rune;
        }),
      ),
    );
    return FilteringTextInputFormatter.digitsOnly.formatEditUpdate(
      oldValue,
      normalized,
    );
  }
}
