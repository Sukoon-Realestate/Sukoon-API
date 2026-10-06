import 'package:equatable/equatable.dart';
import 'package:sokoun_app/features/shared/premium/data/premium_json.dart';
import 'package:sokoun_app/features/tenant/home/data/models/property_search_model.dart';

class PremiumAlertBody extends Equatable {
  const PremiumAlertBody({
    this.name = '',
    this.cadence = '',
    this.filters = const PropertySearchFilters.initial(),
    this.requestKey = '',
  });
  const PremiumAlertBody.initial() : this();
  factory PremiumAlertBody.fromJson(Map<String, dynamic> json) =>
      PremiumAlertBody(
        name: premiumString(json['name']),
        cadence: premiumString(json['cadence']),
        filters: PropertySearchFilters.fromJson(premiumMap(json['filters'])),
        requestKey: premiumString(json['request_key']),
      );
  final String name;
  final String cadence;
  final PropertySearchFilters filters;
  final String requestKey;
  bool get isValid =>
      name.trim().isNotEmpty &&
      name.trim().length <= 80 &&
      filters.hasValidPriceRange &&
      cadence.isNotEmpty &&
      requestKey.isNotEmpty;
  Map<String, dynamic> toJson() => {
    'name': name,
    'cadence': cadence,
    'filters': filters.copyWith(page: 1).toJson(),
    'request_key': requestKey,
  };
  PremiumAlertBody copyWith({
    String? name,
    String? cadence,
    PropertySearchFilters? filters,
    String? requestKey,
  }) => PremiumAlertBody(
    name: name ?? this.name,
    cadence: cadence ?? this.cadence,
    filters: filters ?? this.filters,
    requestKey: requestKey ?? this.requestKey,
  );
  @override
  List<Object?> get props => [name, cadence, filters, requestKey];
}
