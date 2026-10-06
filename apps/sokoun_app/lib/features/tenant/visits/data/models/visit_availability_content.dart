import 'package:equatable/equatable.dart';
import 'visit_schedule_content.dart';

class VisitAvailabilityContent extends Equatable {
  const VisitAvailabilityContent({
    this.days = const [],
    this.times = const [],
    this.isCached = false,
  });
  const VisitAvailabilityContent.initial()
    : days = const [],
      times = const [],
      isCached = false;
  factory VisitAvailabilityContent.fromJson(
    Map<String, dynamic> json,
  ) => VisitAvailabilityContent(
    days: (json['days'] as List? ?? const [])
        .whereType<Map>()
        .map(
          (value) => VisitDayContent.fromJson(Map<String, dynamic>.from(value)),
        )
        .toList(growable: false),
    times: (json['times'] as List? ?? const [])
        .whereType<Map>()
        .map(
          (value) =>
              VisitTimeSlotContent.fromJson(Map<String, dynamic>.from(value)),
        )
        .toList(growable: false),
    isCached: json['is_cached'] == true,
  );
  final List<VisitDayContent> days;
  final List<VisitTimeSlotContent> times;
  final bool isCached;
  Map<String, dynamic> toJson() => {
    'days': days.map((day) => day.toJson()).toList(),
    'times': times.map((time) => time.toJson()).toList(),
    'is_cached': isCached,
  };
  VisitAvailabilityContent copyWith({
    List<VisitDayContent>? days,
    List<VisitTimeSlotContent>? times,
    bool? isCached,
  }) => VisitAvailabilityContent(
    days: days ?? this.days,
    times: times ?? this.times,
    isCached: isCached ?? this.isCached,
  );
  @override
  List<Object?> get props => [days, times, isCached];
}
