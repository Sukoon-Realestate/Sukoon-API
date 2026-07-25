part of '../../imports.dart';

class VisitDayContent {
  const VisitDayContent({
    required this.weekday,
    required this.day,
    required this.month,
  });

  factory VisitDayContent.initial() =>
      const VisitDayContent(weekday: '', day: '', month: '');

  factory VisitDayContent.fromJson(Map<String, dynamic> json) {
    return VisitDayContent(
      weekday: json['weekday'] ?? '',
      day: json['day'] ?? '',
      month: json['month'] ?? '',
    );
  }

  final String weekday;
  final String day;
  final String month;

  String get fullLabel => '$weekday $day $month';

  Map<String, dynamic> toJson() {
    return {'weekday': weekday, 'day': day, 'month': month};
  }

  VisitDayContent copyWith({String? weekday, String? day, String? month}) {
    return VisitDayContent(
      weekday: weekday ?? this.weekday,
      day: day ?? this.day,
      month: month ?? this.month,
    );
  }
}

class VisitTimeSlotContent {
  const VisitTimeSlotContent({required this.label, this.isAvailable = true});

  factory VisitTimeSlotContent.initial() =>
      const VisitTimeSlotContent(label: '');

  factory VisitTimeSlotContent.fromJson(Map<String, dynamic> json) {
    return VisitTimeSlotContent(
      label: json['label'] ?? '',
      isAvailable: json['is_available'] ?? true,
    );
  }

  final String label;
  final bool isAvailable;

  Map<String, dynamic> toJson() {
    return {'label': label, 'is_available': isAvailable};
  }

  VisitTimeSlotContent copyWith({String? label, bool? isAvailable}) {
    return VisitTimeSlotContent(
      label: label ?? this.label,
      isAvailable: isAvailable ?? this.isAvailable,
    );
  }
}
