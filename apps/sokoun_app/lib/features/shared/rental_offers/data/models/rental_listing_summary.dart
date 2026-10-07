import 'package:equatable/equatable.dart';
import '../rental_json.dart';
import '../enums/rental_scope.dart';
import 'package:sokoun_app/features/owner/home/data/enums/property_price_period.dart';
import '../../../finance/data/egyptian_pound.dart';

/// Server projection of eligible offers for the current search, not a client min.
class RentalListingSummary extends Equatable {
  const RentalListingSummary({
    this.count = 0,
    this.scopes = const [],
    this.labels = const [],
    this.price = '',
    this.pricePeriod = '',
    this.priceScope,
    this.startingFrom = false,
  });
  const RentalListingSummary.initial() : this();
  factory RentalListingSummary.fromJson(Map<String, dynamic> json) =>
      RentalListingSummary(
        count: rentalInt(json['eligible_count']),
        scopes: rentalStrings(json['scopes']),
        labels: rentalStrings(json['labels']),
        price: json['price']?.toString() ?? '',
        pricePeriod: json['price_period']?.toString() ?? '',
        priceScope: json['price_scope']?.toString(),
        startingFrom: json['starting_from'] == true,
      );
  static RentalListingSummary? read(Map<String, dynamic> json) {
    final value = json['rental_summary'];
    return value is Map
        ? RentalListingSummary.fromJson(Map<String, dynamic>.from(value))
        : null;
  }

  final int count;
  final List<String> scopes, labels;
  final String price, pricePeriod;
  final String? priceScope;
  final bool startingFrom;
  bool get hasConfirmedPrice {
    final amount = EgyptianPound.parseAmount(price);
    return count > 0 &&
        amount != null &&
        amount.isFinite &&
        amount > 0 &&
        PropertyPricePeriod.fromValue(pricePeriod) != null &&
        RentalScope.fromValue(priceScope) != null;
  }

  bool matchesContext({String scope = '', String period = ''}) =>
      count > 0 &&
      scopes.isNotEmpty &&
      scopes.every((value) => RentalScope.fromValue(value) != null) &&
      (scope.isEmpty || scopes.every((value) => value == scope)) &&
      (price.isEmpty ||
          (hasConfirmedPrice &&
              (scope.isEmpty || priceScope == scope) &&
              (period.isEmpty || pricePeriod == period)));
  Map<String, dynamic> toJson() => {
    'eligible_count': count,
    'scopes': scopes,
    'labels': labels,
    'price': price,
    'price_period': pricePeriod,
    'price_scope': priceScope,
    'starting_from': startingFrom,
  };
  RentalListingSummary copyWith({
    int? count,
    List<String>? scopes,
    List<String>? labels,
    String? price,
    String? pricePeriod,
    String? priceScope,
    bool? startingFrom,
  }) => RentalListingSummary(
    count: count ?? this.count,
    scopes: scopes ?? this.scopes,
    labels: labels ?? this.labels,
    price: price ?? this.price,
    pricePeriod: pricePeriod ?? this.pricePeriod,
    priceScope: priceScope ?? this.priceScope,
    startingFrom: startingFrom ?? this.startingFrom,
  );
  @override
  List<Object?> get props => [
    count,
    scopes,
    labels,
    price,
    pricePeriod,
    priceScope,
    startingFrom,
  ];
}
