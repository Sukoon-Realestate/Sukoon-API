import 'package:equatable/equatable.dart';
import 'package:sokoun_app/features/shared/finance/data/egyptian_pound.dart';
import '../rental_json.dart';

class RentalTerms extends Equatable {
  const RentalTerms({
    this.price = '',
    this.pricePeriod = '',
    this.minimumMonths = 0,
    this.deposit = '',
    this.suitableFor = '',
    this.description = '',
    this.smokingAllowed,
    this.rules = const [],
  });
  const RentalTerms.initial() : this();
  factory RentalTerms.fromJson(Map<String, dynamic> json) => RentalTerms(
    price: json['price']?.toString() ?? '',
    pricePeriod: json['price_period']?.toString() ?? '',
    minimumMonths: rentalInt(json['rental_period']),
    deposit: json['deposit']?.toString() ?? '',
    suitableFor: json['suitable_for']?.toString() ?? '',
    description: json['description']?.toString() ?? '',
    smokingAllowed: json['smoking_allowed'] is bool
        ? json['smoking_allowed'] as bool
        : null,
    rules: rentalStrings(json['rules']),
  );

  final String price, pricePeriod, deposit, suitableFor, description;
  final int minimumMonths;
  final bool? smokingAllowed;
  final List<String> rules;
  static const inheritedFields = {
    'rental_period',
    'deposit',
    'suitable_for',
    'description',
    'smoking_allowed',
    'rules',
  };
  bool get hasValidPrice {
    final amount = EgyptianPound.parseAmount(price);
    return amount != null && amount.isFinite && amount > 0;
  }

  bool get hasValidDeposit =>
      deposit.isEmpty ||
      const {
        'none',
        'half_month',
        'one_month',
        'two_months',
      }.contains(deposit) ||
      (EgyptianPound.parseAmount(deposit)?.isFinite == true &&
          EgyptianPound.parseAmount(deposit)! >= 0);
  bool get isValid =>
      hasValidPrice &&
      const {'daily', 'weekly', 'monthly', 'yearly'}.contains(pricePeriod) &&
      minimumMonths > 0 &&
      hasValidDeposit &&
      description.trim().length >= 10 &&
      const {
        'all',
        'families',
        'singles',
        'students',
        'female_students',
      }.contains(suitableFor);

  RentalTerms resolve(RentalTerms defaults, Set<String> inherited) =>
      RentalTerms.fromJson({
        ...toJson(),
        for (final field in inherited.intersection(inheritedFields))
          field: defaults.toJson()[field],
      });
  Map<String, dynamic> toJson() => {
    'price': price.trim(),
    'price_period': pricePeriod,
    'rental_period': minimumMonths,
    'deposit': deposit.trim(),
    'suitable_for': suitableFor,
    'description': description.trim(),
    'smoking_allowed': smokingAllowed,
    'rules': rules,
  };
  Map<String, dynamic> toDefaultsJson() => toJson()
    ..remove('price')
    ..remove('price_period');
  RentalTerms copyWith({
    String? price,
    String? pricePeriod,
    int? minimumMonths,
    String? deposit,
    String? suitableFor,
    String? description,
    bool? smokingAllowed,
    bool clearSmoking = false,
    List<String>? rules,
  }) => RentalTerms(
    price: price ?? this.price,
    pricePeriod: pricePeriod ?? this.pricePeriod,
    minimumMonths: minimumMonths ?? this.minimumMonths,
    deposit: deposit ?? this.deposit,
    suitableFor: suitableFor ?? this.suitableFor,
    description: description ?? this.description,
    smokingAllowed: clearSmoking ? null : smokingAllowed ?? this.smokingAllowed,
    rules: rules ?? this.rules,
  );
  @override
  List<Object?> get props => [
    price,
    pricePeriod,
    minimumMonths,
    deposit,
    suitableFor,
    description,
    smokingAllowed,
    rules,
  ];
}
