part of '../../imports.dart';

class VisitDayContent {
  const VisitDayContent({
    required this.weekday,
    required this.day,
    required this.month,
    required this.visitDate,
  });

  factory VisitDayContent.initial() =>
      const VisitDayContent(weekday: '', day: '', month: '', visitDate: '');

  factory VisitDayContent.fromJson(Map<String, dynamic> json) {
    return VisitDayContent(
      weekday: json['weekday'] ?? '',
      day: json['day'] ?? '',
      month: json['month'] ?? '',
      visitDate: json['visit_date'] ?? '',
    );
  }

  final String weekday;
  final String day;
  final String month;
  final String visitDate;

  String get fullLabel => '$weekday $day $month';

  Map<String, dynamic> toJson() {
    return {
      'weekday': weekday,
      'day': day,
      'month': month,
      'visit_date': visitDate,
    };
  }

  VisitDayContent copyWith({
    String? weekday,
    String? day,
    String? month,
    String? visitDate,
  }) {
    return VisitDayContent(
      weekday: weekday ?? this.weekday,
      day: day ?? this.day,
      month: month ?? this.month,
      visitDate: visitDate ?? this.visitDate,
    );
  }
}

class VisitTimeSlotContent {
  const VisitTimeSlotContent({
    required this.label,
    required this.visitTime,
    this.isAvailable = true,
  });

  factory VisitTimeSlotContent.initial() =>
      const VisitTimeSlotContent(label: '', visitTime: '');

  factory VisitTimeSlotContent.fromJson(Map<String, dynamic> json) {
    return VisitTimeSlotContent(
      label: json['label'] ?? '',
      visitTime: json['visit_time'] ?? '',
      isAvailable: json['is_available'] ?? true,
    );
  }

  final String label;
  final String visitTime;
  final bool isAvailable;

  Map<String, dynamic> toJson() {
    return {
      'label': label,
      'visit_time': visitTime,
      'is_available': isAvailable,
    };
  }

  VisitTimeSlotContent copyWith({
    String? label,
    String? visitTime,
    bool? isAvailable,
  }) {
    return VisitTimeSlotContent(
      label: label ?? this.label,
      visitTime: visitTime ?? this.visitTime,
      isAvailable: isAvailable ?? this.isAvailable,
    );
  }
}
