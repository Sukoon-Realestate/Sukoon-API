import 'package:sokoun_app/features/shared/rental_offers/data/models/rental_selection.dart';
import 'package:equatable/equatable.dart';
import 'package:sokoun_app/features/shared/finance/data/egyptian_pound.dart';
import 'package:sokoun_app/features/tenant/home/data/models/property_details_model.dart';

class PropertyCostBreakdown extends Equatable {
  const PropertyCostBreakdown({this.rent, this.deposit, this.period = ''});
  const PropertyCostBreakdown.initial()
    : rent = null,
      deposit = null,
      period = '';
  factory PropertyCostBreakdown.fromProperty(
    PropertyDetailsModel property, {
    RentalSelection? selection,
  }) {
    if (property.rentalInventory != null &&
        (selection == null ||
            selection.propertyId != property.id ||
            !selection.canIdentify)) {
      return const PropertyCostBreakdown.initial();
    }
    return PropertyCostBreakdown.fromAmounts(
      price: selection?.terms.price ?? property.price,
      pricePeriod: selection?.terms.pricePeriod ?? property.pricePeriod,
      depositValue: selection?.terms.deposit ?? property.deposit,
    );
  }
  factory PropertyCostBreakdown.fromAmounts({
    required String price,
    required String pricePeriod,
    required String depositValue,
  }) {
    final amount = EgyptianPound.parseAmount(price)?.toDouble();
    final rent = amount != null && amount > 0 ? amount : null;
    final customDeposit = EgyptianPound.parseAmount(depositValue)?.toDouble();
    final double? deposit = switch (depositValue) {
      'none' => 0,
      'half_month' =>
        pricePeriod == 'monthly' && rent != null ? rent / 2 : null,
      'one_month' => pricePeriod == 'monthly' ? rent : null,
      'two_months' =>
        pricePeriod == 'monthly' && rent != null ? rent * 2 : null,
      _ => customDeposit != null && customDeposit >= 0 ? customDeposit : null,
    };
    return PropertyCostBreakdown(
      rent: rent,
      deposit: deposit,
      period: pricePeriod,
    );
  }
  factory PropertyCostBreakdown.fromJson(Map<String, dynamic> json) =>
      PropertyCostBreakdown(
        rent: (json['rent'] as num?)?.toDouble(),
        deposit: (json['deposit'] as num?)?.toDouble(),
        period: json['period'] as String? ?? '',
      );
  final double? rent;
  final double? deposit;
  final String period;
  double? get knownSubtotal =>
      rent != null && deposit != null ? rent! + deposit! : null;
  Map<String, dynamic> toJson() => {
    'rent': rent,
    'deposit': deposit,
    'period': period,
  };
  PropertyCostBreakdown copyWith({
    double? rent,
    double? deposit,
    String? period,
  }) => PropertyCostBreakdown(
    rent: rent ?? this.rent,
    deposit: deposit ?? this.deposit,
    period: period ?? this.period,
  );
  @override
  List<Object?> get props => [rent, deposit, period];
}
