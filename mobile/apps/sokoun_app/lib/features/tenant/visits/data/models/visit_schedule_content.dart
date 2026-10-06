import 'package:equatable/equatable.dart';
import 'package:melos_core/config/language/locale_keys.g.dart';

class VisitDayContent extends Equatable {
  const VisitDayContent({
    required this.weekday,
    required this.day,
    required this.month,
    required this.visitDate,
  });

  const VisitDayContent.initial()
    : weekday = '',
      day = '',
      month = '',
      visitDate = '';

  factory VisitDayContent.fromJson(Map<String, dynamic> json) {
    final String date = json['date'] as String? ?? '';
    final List<String> dateParts = date.split('/');
    return VisitDayContent(
      weekday: json['day'] as String? ?? json['weekday'] as String? ?? '',
      day: dateParts.isNotEmpty ? dateParts.first : '',
      month: dateParts.length > 1 ? dateParts[1] : '',
      visitDate: json['visit_date'] as String? ?? '',
    );
  }

  final String weekday;
  final String day;
  final String month;
  final String visitDate;

  String get dateLabel =>
      [day, month].where((part) => part.isNotEmpty).join('/');

  String get weekdayLabel {
    switch (weekday.toLowerCase()) {
      case 'friday':
        return LocaleKeys.tenantVisitDayFriday;
      case 'saturday':
        return LocaleKeys.tenantVisitDaySaturday;
      case 'sunday':
        return LocaleKeys.tenantVisitDaySunday;
      case 'monday':
        return LocaleKeys.tenantVisitDayMonday;
      case 'tuesday':
        return LocaleKeys.tenantVisitDayTuesday;
      case 'wednesday':
        return LocaleKeys.tenantVisitDayWednesday;
      case 'thursday':
        return LocaleKeys.tenantVisitDayThursday;
      default:
        return weekday;
    }
  }

  String get fullLabel => '$weekdayLabel $day $month'.trim();

  Map<String, dynamic> toJson() => {
    'day': weekday,
    'date': dateLabel,
    'visit_date': visitDate,
  };

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

  @override
  List<Object?> get props => [weekday, day, month, visitDate];
}

class VisitTimeSlotContent extends Equatable {
  const VisitTimeSlotContent({
    required this.label,
    required this.visitTime,
    this.isAvailable = true,
  });

  const VisitTimeSlotContent.initial()
    : label = '',
      visitTime = '',
      isAvailable = true;

  factory VisitTimeSlotContent.fromJson(Map<String, dynamic> json) {
    return VisitTimeSlotContent(
      label: json['time'] as String? ?? json['label'] as String? ?? '',
      visitTime: json['visit_time'] as String? ?? '',
      isAvailable: json['is_available'] as bool? ?? false,
    );
  }

  final String label;
  final String visitTime;
  final bool isAvailable;

  Map<String, dynamic> toJson() => {
    'time': label,
    'visit_time': visitTime,
    'is_available': isAvailable,
  };

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

  @override
  List<Object?> get props => [label, visitTime, isAvailable];
}
