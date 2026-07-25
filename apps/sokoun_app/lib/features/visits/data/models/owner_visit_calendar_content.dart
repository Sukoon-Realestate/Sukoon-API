part of '../../imports.dart';

class OwnerCalendarVisitContent {
  const OwnerCalendarVisitContent({
    required this.id,
    required this.initial,
    required this.name,
    required this.time,
    required this.status,
  });

  factory OwnerCalendarVisitContent.initial() =>
      const OwnerCalendarVisitContent(
        id: '',
        initial: '',
        name: '',
        time: '',
        status: OwnerVisitRequestStatus.pending,
      );

  factory OwnerCalendarVisitContent.fromJson(Map<String, dynamic> json) {
    return OwnerCalendarVisitContent(
      id: json['id'] ?? '',
      initial: json['initial'] ?? '',
      name: json['name'] ?? '',
      time: json['time'] ?? '',
      status: OwnerVisitRequestStatus.values.firstWhere(
        (status) => status.name == json['status'],
        orElse: () => OwnerVisitRequestStatus.pending,
      ),
    );
  }

  final String id;
  final String initial;
  final String name;
  final String time;
  final OwnerVisitRequestStatus status;

  Map<String, dynamic> toJson() {
    return {
      'id': id,
      'initial': initial,
      'name': name,
      'time': time,
      'status': status.name,
    };
  }

  OwnerCalendarVisitContent copyWith({
    String? id,
    String? initial,
    String? name,
    String? time,
    OwnerVisitRequestStatus? status,
  }) {
    return OwnerCalendarVisitContent(
      id: id ?? this.id,
      initial: initial ?? this.initial,
      name: name ?? this.name,
      time: time ?? this.time,
      status: status ?? this.status,
    );
  }
}

class OwnerAvailabilityDayContent {
  const OwnerAvailabilityDayContent({
    required this.weekday,
    required this.shortWeekday,
    required this.day,
  });

  factory OwnerAvailabilityDayContent.initial() =>
      const OwnerAvailabilityDayContent(weekday: '', shortWeekday: '', day: '');

  factory OwnerAvailabilityDayContent.fromJson(Map<String, dynamic> json) {
    return OwnerAvailabilityDayContent(
      weekday: json['weekday'] ?? '',
      shortWeekday: json['short_weekday'] ?? '',
      day: json['day'] ?? '',
    );
  }

  final String weekday;
  final String shortWeekday;
  final String day;

  Map<String, dynamic> toJson() {
    return {'weekday': weekday, 'short_weekday': shortWeekday, 'day': day};
  }

  OwnerAvailabilityDayContent copyWith({
    String? weekday,
    String? shortWeekday,
    String? day,
  }) {
    return OwnerAvailabilityDayContent(
      weekday: weekday ?? this.weekday,
      shortWeekday: shortWeekday ?? this.shortWeekday,
      day: day ?? this.day,
    );
  }
}

abstract final class OwnerVisitCalendarContent {
  static const List<int?> monthDays = [
    null,
    null,
    1,
    2,
    3,
    4,
    5,
    6,
    7,
    8,
    9,
    10,
    11,
    12,
    13,
    14,
    15,
    16,
    17,
    18,
    19,
    20,
    21,
    22,
    23,
    24,
    25,
    26,
    27,
    28,
    29,
    30,
    31,
    null,
    null,
  ];

  static const Set<int> daysWithVisits = {5, 8, 12, 15, 19, 22, 26};

  static List<String> get weekdayHeaders => [
    LocaleKeys.ownerCalendarDaySundayShort,
    LocaleKeys.ownerCalendarDayMondayShort,
    LocaleKeys.ownerCalendarDayTuesdayShort,
    LocaleKeys.ownerCalendarDayWednesdayShort,
    LocaleKeys.ownerCalendarDayThursdayShort,
    LocaleKeys.ownerCalendarDayFridayShort,
    LocaleKeys.ownerCalendarDaySaturdayShort,
  ];

  static List<OwnerCalendarVisitContent> get visits => [
    OwnerCalendarVisitContent(
      id: 'calendar-mohamed',
      initial: LocaleKeys.ownerVisitTenantMohamedInitial,
      name: LocaleKeys.ownerVisitTenantMohamed,
      time: LocaleKeys.ownerVisitTimeThreePm,
      status: OwnerVisitRequestStatus.accepted,
    ),
    OwnerCalendarVisitContent(
      id: 'calendar-sara',
      initial: LocaleKeys.ownerVisitTenantSaraInitial,
      name: LocaleKeys.ownerCalendarTenantSaraMahmoud,
      time: LocaleKeys.ownerCalendarTimeFiveThirty,
      status: OwnerVisitRequestStatus.pending,
    ),
  ];

  static List<OwnerAvailabilityDayContent> get availabilityDays => [
    OwnerAvailabilityDayContent(
      weekday: LocaleKeys.ownerAvailabilitySunday,
      shortWeekday: LocaleKeys.ownerAvailabilitySundayShort,
      day: '14',
    ),
    OwnerAvailabilityDayContent(
      weekday: LocaleKeys.ownerAvailabilityMonday,
      shortWeekday: LocaleKeys.ownerAvailabilityMondayShort,
      day: '15',
    ),
    OwnerAvailabilityDayContent(
      weekday: LocaleKeys.ownerAvailabilityTuesday,
      shortWeekday: LocaleKeys.ownerAvailabilityTuesdayShort,
      day: '16',
    ),
    OwnerAvailabilityDayContent(
      weekday: LocaleKeys.ownerAvailabilityWednesday,
      shortWeekday: LocaleKeys.ownerAvailabilityWednesdayShort,
      day: '17',
    ),
    OwnerAvailabilityDayContent(
      weekday: LocaleKeys.ownerAvailabilityThursday,
      shortWeekday: LocaleKeys.ownerAvailabilityThursdayShort,
      day: '18',
    ),
    OwnerAvailabilityDayContent(
      weekday: LocaleKeys.ownerAvailabilityFriday,
      shortWeekday: LocaleKeys.ownerAvailabilityFridayShort,
      day: '19',
    ),
    OwnerAvailabilityDayContent(
      weekday: LocaleKeys.ownerAvailabilitySaturday,
      shortWeekday: LocaleKeys.ownerAvailabilitySaturdayShort,
      day: '20',
    ),
  ];

  static List<String> get availabilityTimes => [
    LocaleKeys.ownerAvailabilityTimeNineAm,
    LocaleKeys.ownerAvailabilityTimeTenAm,
    LocaleKeys.ownerAvailabilityTimeElevenAm,
    LocaleKeys.ownerAvailabilityTimeNoon,
    LocaleKeys.ownerAvailabilityTimeTwoPm,
    LocaleKeys.ownerAvailabilityTimeThreePm,
    LocaleKeys.ownerAvailabilityTimeFourPm,
    LocaleKeys.ownerAvailabilityTimeFivePm,
  ];
}
