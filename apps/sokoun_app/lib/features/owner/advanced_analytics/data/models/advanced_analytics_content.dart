import 'package:equatable/equatable.dart';
import 'package:sokoun_app/features/shared/premium/data/premium_json.dart';
import 'analytics_metric.dart';

class AdvancedAnalyticsContent extends Equatable {
  const AdvancedAnalyticsContent({
    this.propertyId = '',
    this.periodDays = 30,
    this.measuredAt,
    this.metrics = const [],
    this.exportUrl = '',
    this.methodology = '',
  });
  const AdvancedAnalyticsContent.initial() : this();
  factory AdvancedAnalyticsContent.fromJson(Map<String, dynamic> json) =>
      AdvancedAnalyticsContent(
        propertyId: premiumString(json['property_id']),
        periodDays: premiumInt(json['period_days']) ?? 30,
        measuredAt: premiumDate(json['measured_at']),
        metrics: premiumMaps(
          json['metrics'],
        ).map(AnalyticsMetric.fromJson).toList(growable: false),
        exportUrl: premiumString(json['export_url']),
        methodology: premiumString(json['methodology']),
      );
  final String propertyId;
  final int periodDays;
  final DateTime? measuredAt;
  final List<AnalyticsMetric> metrics;
  final String exportUrl;
  final String methodology;

  Map<String, dynamic> toJson() => {
    'property_id': propertyId,
    'period_days': periodDays,
    'measured_at': measuredAt?.toIso8601String(),
    'metrics': metrics.map((item) => item.toJson()).toList(growable: false),
    'export_url': exportUrl,
    'methodology': methodology,
  };
  AdvancedAnalyticsContent copyWith({
    String? propertyId,
    int? periodDays,
    DateTime? measuredAt,
    List<AnalyticsMetric>? metrics,
    String? exportUrl,
    String? methodology,
  }) => AdvancedAnalyticsContent(
    propertyId: propertyId ?? this.propertyId,
    periodDays: periodDays ?? this.periodDays,
    measuredAt: measuredAt ?? this.measuredAt,
    metrics: metrics ?? this.metrics,
    exportUrl: exportUrl ?? this.exportUrl,
    methodology: methodology ?? this.methodology,
  );
  @override
  List<Object?> get props => [
    propertyId,
    periodDays,
    measuredAt,
    metrics,
    exportUrl,
    methodology,
  ];
}
