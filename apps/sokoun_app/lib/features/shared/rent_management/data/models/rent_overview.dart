import 'package:equatable/equatable.dart';
import 'package:sokoun_app/features/shared/premium/data/premium_json.dart';
import 'rent_invoice.dart';

/// One server-selected due invoice, not a locally calculated rent balance.
class RentOverview extends Equatable {
  const RentOverview({
    this.results = const [],
    this.count,
    this.hasResults = false,
  });
  const RentOverview.initial() : this();

  factory RentOverview.fromJson(Map<String, dynamic> json) => RentOverview(
    results: premiumMaps(json['results']).map(RentInvoice.fromJson).toList(),
    count: premiumInt(json['count']),
    hasResults:
        json['results'] is List &&
        (json['results'] as List).every((item) => item is Map),
  );

  final List<RentInvoice> results;
  final int? count;
  final bool hasResults;
  RentInvoice? get invoice => results.firstOrNull;
  bool get isValid =>
      hasResults &&
      count != null &&
      count! >= 0 &&
      results.length <= 1 &&
      (count == 0 ? results.isEmpty : results.isNotEmpty) &&
      results.every(
        (invoice) =>
            invoice.id.isNotEmpty &&
            invoice.leaseId.isNotEmpty &&
            invoice.status.isPayable,
      );

  Map<String, dynamic> toJson() => {
    if (hasResults) 'results': results.map((item) => item.toJson()).toList(),
    'count': count,
  };
  RentOverview copyWith({
    List<RentInvoice>? results,
    int? count,
    bool? hasResults,
  }) => RentOverview(
    results: results ?? this.results,
    count: count ?? this.count,
    hasResults: hasResults ?? this.hasResults,
  );
  @override
  List<Object?> get props => [results, count, hasResults];
}
