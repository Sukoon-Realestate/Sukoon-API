/// Sokoun prices and financial amounts are denominated in Egyptian pounds.
abstract final class EgyptianPound {
  static const String code = 'EGP';

  static num? parseAmount(Object? value) {
    if (value is num) return value.isFinite ? value : null;
    if (value is! String) return null;
    final text = String.fromCharCodes(
      value.trim().runes.map((rune) {
        if (rune >= 0x0660 && rune <= 0x0669) return rune - 0x0660 + 0x30;
        if (rune >= 0x06f0 && rune <= 0x06f9) return rune - 0x06f0 + 0x30;
        return rune;
      }),
    ).replaceAll(RegExp('[,٬]'), '').replaceAll('٫', '.');
    final amount = num.tryParse(text);
    return amount != null && amount.isFinite ? amount : null;
  }

  /// Group pounds and retain up to two decimal places for piastres.
  static String formatAmount(Object? value) {
    final amount = parseAmount(value);
    if (amount == null) return '—';
    final parts = amount
        .toStringAsFixed(2)
        .replaceFirst(RegExp(r'\.?0+$'), '')
        .split('.');
    final whole = parts.first.replaceAllMapped(
      RegExp(r'(\d)(?=(\d{3})+(?!\d))'),
      (match) => '${match[1]},',
    );
    return parts.length > 1 ? '$whole.${parts.last}' : whole;
  }
}
