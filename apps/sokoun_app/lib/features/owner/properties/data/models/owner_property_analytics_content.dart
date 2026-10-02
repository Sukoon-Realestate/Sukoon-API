import '../owner_property_json.dart';
import 'package:equatable/equatable.dart';

class OwnerAnalyticsDay extends Equatable {
  const OwnerAnalyticsDay({required this.date, required this.count});
  const OwnerAnalyticsDay.initial() : date = '', count = 0;
  factory OwnerAnalyticsDay.fromJson(Map<String, dynamic> json) =>
      OwnerAnalyticsDay(
        date: json['date']?.toString() ?? '',
        count: ownerPropertyNumber(json['count']).toInt(),
      );
  final String date;
  final int count;
  Map<String, dynamic> toJson() => {'date': date, 'count': count};
  OwnerAnalyticsDay copyWith({String? date, int? count}) =>
      OwnerAnalyticsDay(date: date ?? this.date, count: count ?? this.count);
  @override
  List<Object?> get props => [date, count];
}

class OwnerSearchCriterion extends Equatable {
  const OwnerSearchCriterion({
    required this.key,
    required this.label,
    required this.percentage,
  });
  const OwnerSearchCriterion.initial() : key = '', label = '', percentage = 0;
  factory OwnerSearchCriterion.fromJson(Map<String, dynamic> json) =>
      OwnerSearchCriterion(
        key: json['key']?.toString() ?? '',
        label: json['label']?.toString() ?? '',
        percentage: ownerPropertyNumber(json['percentage']).toDouble(),
      );
  final String key, label;
  final double percentage;
  Map<String, dynamic> toJson() => {
    'key': key,
    'label': label,
    'percentage': percentage,
  };
  OwnerSearchCriterion copyWith({
    String? key,
    String? label,
    double? percentage,
  }) => OwnerSearchCriterion(
    key: key ?? this.key,
    label: label ?? this.label,
    percentage: percentage ?? this.percentage,
  );
  @override
  List<Object?> get props => [key, label, percentage];
}

class OwnerPropertyAnalyticsContent extends Equatable {
  const OwnerPropertyAnalyticsContent({
    this.hasDetails = true,
    required this.views,
    required this.visitRequests,
    required this.saves,
    required this.acceptanceRate,
    this.period = '30_days',
    this.periodLabel = '',
    this.history = const [],
    this.criteria = const [],
  });
  const OwnerPropertyAnalyticsContent.initial()
    : hasDetails = false,
      views = 0,
      visitRequests = 0,
      saves = 0,
      acceptanceRate = 0,
      period = '30_days',
      periodLabel = '',
      history = const [],
      criteria = const [];

  factory OwnerPropertyAnalyticsContent.fromJson(
    Map<String, dynamic> json,
  ) => OwnerPropertyAnalyticsContent(
    hasDetails:
        json['has_details'] as bool? ??
        const [
          'views_count',
          'visit_requests_count',
          'saved_count',
          'acceptance_rate',
        ].every((key) => json[key] != null),
    views: ownerPropertyNumber(json['views_count'] ?? json['views']).toInt(),
    visitRequests: ownerPropertyNumber(json['visit_requests_count']).toInt(),
    saves: ownerPropertyNumber(json['saved_count']).toInt(),
    acceptanceRate: ownerPropertyNumber(json['acceptance_rate']).toDouble(),
    period: json['period']?.toString() ?? '30_days',
    periodLabel: json['period_label']?.toString() ?? '',
    history: ownerPropertyMaps(
      json['views_last_14_days'],
    ).map(OwnerAnalyticsDay.fromJson).toList(growable: false),
    criteria: ownerPropertyMaps(
      json['top_search_criteria'],
    ).map(OwnerSearchCriterion.fromJson).toList(growable: false),
  );

  final bool hasDetails;
  final int views, visitRequests, saves;
  final double acceptanceRate;
  final String period, periodLabel;
  final List<OwnerAnalyticsDay> history;
  final List<OwnerSearchCriterion> criteria;
  List<int> get viewHistory =>
      history.map((day) => day.count).toList(growable: false);

  Map<String, dynamic> toJson() => {
    'has_details': hasDetails,
    'views_count': views,
    'visit_requests_count': visitRequests,
    'saved_count': saves,
    'acceptance_rate': acceptanceRate,
    'period': period,
    'period_label': periodLabel,
    'views_last_14_days': history
        .map((day) => day.toJson())
        .toList(growable: false),
    'top_search_criteria': criteria
        .map((item) => item.toJson())
        .toList(growable: false),
  };
  OwnerPropertyAnalyticsContent copyWith({
    bool? hasDetails,
    int? views,
    int? visitRequests,
    int? saves,
    double? acceptanceRate,
    String? period,
    String? periodLabel,
    List<OwnerAnalyticsDay>? history,
    List<OwnerSearchCriterion>? criteria,
  }) => OwnerPropertyAnalyticsContent(
    hasDetails: hasDetails ?? this.hasDetails,
    views: views ?? this.views,
    visitRequests: visitRequests ?? this.visitRequests,
    saves: saves ?? this.saves,
    acceptanceRate: acceptanceRate ?? this.acceptanceRate,
    period: period ?? this.period,
    periodLabel: periodLabel ?? this.periodLabel,
    history: history ?? this.history,
    criteria: criteria ?? this.criteria,
  );
  @override
  List<Object?> get props => [
    hasDetails,
    views,
    visitRequests,
    saves,
    acceptanceRate,
    period,
    periodLabel,
    history,
    criteria,
  ];
}
