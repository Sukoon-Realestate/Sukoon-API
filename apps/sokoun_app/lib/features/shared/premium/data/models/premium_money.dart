import 'package:equatable/equatable.dart';
import '../premium_json.dart';

class PremiumMoney extends Equatable {
  const PremiumMoney({this.amountMinor, this.currency = '', this.exponent = 2});
  const PremiumMoney.initial() : this();
  factory PremiumMoney.fromJson(Map<String, dynamic> json) => PremiumMoney(
    amountMinor: premiumInt(json['amount_minor']),
    currency: premiumString(json['currency']),
    exponent: json['exponent'] == null ? 2 : premiumInt(json['exponent']) ?? -1,
  );
  final int? amountMinor;
  final String currency;
  final int exponent;
  bool get isKnown =>
      amountMinor != null &&
      amountMinor! >= 0 &&
      RegExp(r'^[A-Z]{3}$').hasMatch(currency) &&
      exponent >= 0 &&
      exponent <= 3;
  String get display {
    if (!isKnown) return '—';
    final digits = amountMinor!.toString().padLeft(exponent + 1, '0');
    final whole = exponent == 0
        ? digits
        : digits.substring(0, digits.length - exponent);
    final grouped = whole.replaceAllMapped(
      RegExp(r'(\d)(?=(\d{3})+(?!\d))'),
      (match) => '${match[1]},',
    );
    return '$grouped${exponent == 0 ? '' : '.${digits.substring(digits.length - exponent)}'} $currency';
  }

  Map<String, dynamic> toJson() => {
    'amount_minor': amountMinor,
    'currency': currency,
    'exponent': exponent,
  };
  PremiumMoney copyWith({int? amountMinor, String? currency, int? exponent}) =>
      PremiumMoney(
        amountMinor: amountMinor ?? this.amountMinor,
        currency: currency ?? this.currency,
        exponent: exponent ?? this.exponent,
      );
  @override
  List<Object?> get props => [amountMinor, currency, exponent];
}
