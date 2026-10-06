import 'package:equatable/equatable.dart';
import 'package:sokoun_app/features/shared/premium/data/premium_json.dart';

class AnalyticsMetric extends Equatable {
  const AnalyticsMetric({
    this.key = '',
    this.label = '',
    this.definition = '',
    this.unit = '',
    this.value,
  });
  const AnalyticsMetric.initial() : this();
  factory AnalyticsMetric.fromJson(Map<String, dynamic> json) =>
      AnalyticsMetric(
        key: premiumString(json['key']),
        label: premiumString(json['label']),
        definition: premiumString(json['definition']),
        value: _finiteNumber(json['value']),
        unit: premiumString(json['unit']),
      );
  final String key;
  final String label;
  final String definition;
  final num? value;
  final String unit;
  static num? _finiteNumber(Object? value) {
    final parsed = value is num ? value : num.tryParse('$value');
    return parsed != null && parsed.isFinite ? parsed : null;
  }

  String get display => value == null
      ? '—'
      : '${value.toString()}${unit == 'percent' ? '%' : ''}';
  Map<String, dynamic> toJson() => {
    'key': key,
    'label': label,
    'definition': definition,
    'unit': unit,
    'value': value,
  };
  AnalyticsMetric copyWith({
    String? key,
    String? label,
    String? definition,
    num? value,
    String? unit,
  }) => AnalyticsMetric(
    key: key ?? this.key,
    label: label ?? this.label,
    definition: definition ?? this.definition,
    value: value ?? this.value,
    unit: unit ?? this.unit,
  );
  @override
  List<Object?> get props => [key, label, definition, value, unit];
}
