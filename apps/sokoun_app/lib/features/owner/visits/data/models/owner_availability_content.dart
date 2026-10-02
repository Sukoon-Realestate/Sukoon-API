part of '../../imports.dart';

class OwnerAvailabilitySaveBody extends Equatable {
  const OwnerAvailabilitySaveBody({
    required this.availabilityDate,
    required this.slots,
  });

  const OwnerAvailabilitySaveBody.initial()
    : availabilityDate = '',
      slots = const [];

  final String availabilityDate;
  final List<OwnerAvailabilitySlotBody> slots;

  Map<String, dynamic> toJson() => {
    'availability_date': availabilityDate,
    'slots': slots.map((slot) => slot.toJson()).toList(growable: false),
  };

  OwnerAvailabilitySaveBody copyWith({
    String? availabilityDate,
    List<OwnerAvailabilitySlotBody>? slots,
  }) {
    return OwnerAvailabilitySaveBody(
      availabilityDate: availabilityDate ?? this.availabilityDate,
      slots: slots ?? this.slots,
    );
  }

  @override
  List<Object?> get props => [availabilityDate, slots];
}

class OwnerAvailabilitySlotBody extends Equatable {
  const OwnerAvailabilitySlotBody({
    required this.time,
    required this.isEnabled,
  });

  const OwnerAvailabilitySlotBody.initial() : time = '', isEnabled = false;

  final String time;
  final bool isEnabled;

  Map<String, dynamic> toJson() => {'time': time, 'is_enabled': isEnabled};

  OwnerAvailabilitySlotBody copyWith({String? time, bool? isEnabled}) {
    return OwnerAvailabilitySlotBody(
      time: time ?? this.time,
      isEnabled: isEnabled ?? this.isEnabled,
    );
  }

  @override
  List<Object?> get props => [time, isEnabled];
}

class OwnerAvailabilityScheduleContent extends Equatable {
  const OwnerAvailabilityScheduleContent({
    required this.weekStart,
    required this.weekEnd,
    required this.days,
  });

  const OwnerAvailabilityScheduleContent.initial()
    : weekStart = '',
      weekEnd = '',
      days = const [];

  factory OwnerAvailabilityScheduleContent.fromJson(Map<String, dynamic> json) {
    return OwnerAvailabilityScheduleContent(
      weekStart: json['week_start'] as String? ?? '',
      weekEnd: json['week_end'] as String? ?? '',
      days:
          (json['days'] as List?)
              ?.whereType<Map<String, dynamic>>()
              .map(OwnerAvailabilityDayContent.fromJson)
              .toList(growable: false) ??
          const [],
    );
  }

  final String weekStart;
  final String weekEnd;
  final List<OwnerAvailabilityDayContent> days;

  static DateTime startOfWeek(DateTime date) => DateTime(
    date.year,
    date.month,
    date.day - (date.weekday - DateTime.monday),
  );

  OwnerAvailabilityScheduleContent withEditableDays() {
    final start = DateTime.tryParse(weekStart);
    final end = DateTime.tryParse(weekEnd);
    // Dates are calendar days; a daylight-saving week need not be 144 hours.
    if (start == null ||
        end == null ||
        !DateUtils.isSameDay(
          end,
          DateTime(start.year, start.month, start.day + 6),
        )) {
      return this;
    }
    return copyWith(
      days: List.generate(7, (index) {
        final date = DateTime(start.year, start.month, start.day + index);
        final key = OwnerVisitCalendarContent.formatDate(date);
        return days.where((day) => day.date == key).firstOrNull ??
            OwnerAvailabilityDayContent.fromDate(date);
      }, growable: false),
    );
  }

  Map<String, dynamic> toJson() => {
    'week_start': weekStart,
    'week_end': weekEnd,
    'days': days.map((day) => day.toJson()).toList(growable: false),
  };

  OwnerAvailabilityScheduleContent copyWith({
    String? weekStart,
    String? weekEnd,
    List<OwnerAvailabilityDayContent>? days,
  }) {
    return OwnerAvailabilityScheduleContent(
      weekStart: weekStart ?? this.weekStart,
      weekEnd: weekEnd ?? this.weekEnd,
      days: days ?? this.days,
    );
  }

  @override
  List<Object?> get props => [weekStart, weekEnd, days];
}

class OwnerAvailabilityDayContent extends Equatable {
  const OwnerAvailabilityDayContent({
    required this.date,
    required this.dayName,
    required this.slots,
  });

  const OwnerAvailabilityDayContent.initial()
    : date = '',
      dayName = '',
      slots = const [];

  factory OwnerAvailabilityDayContent.fromDate(DateTime date) {
    return OwnerAvailabilityDayContent(
      date: OwnerVisitCalendarContent.formatDate(date),
      dayName: _ownerAvailabilityDayName(date.weekday),
      slots: const [],
    );
  }

  factory OwnerAvailabilityDayContent.fromJson(Map<String, dynamic> json) {
    return OwnerAvailabilityDayContent(
      date: json['date'] as String? ?? '',
      dayName: json['day'] as String? ?? '',
      slots:
          (json['slots'] as List?)
              ?.whereType<Map<String, dynamic>>()
              .map(OwnerAvailabilitySlotContent.fromJson)
              .toList(growable: false) ??
          const [],
    );
  }

  final String date;
  final String dayName;
  final List<OwnerAvailabilitySlotContent> slots;

  DateTime? get dateValue => DateTime.tryParse(date);

  Map<String, dynamic> toJson() => {
    'date': date,
    'day': dayName,
    'slots': slots.map((slot) => slot.toJson()).toList(growable: false),
  };

  OwnerAvailabilityDayContent copyWith({
    String? date,
    String? dayName,
    List<OwnerAvailabilitySlotContent>? slots,
  }) {
    return OwnerAvailabilityDayContent(
      date: date ?? this.date,
      dayName: dayName ?? this.dayName,
      slots: slots ?? this.slots,
    );
  }

  @override
  List<Object?> get props => [date, dayName, slots];
}

class OwnerAvailabilitySlotContent extends Equatable {
  const OwnerAvailabilitySlotContent({
    required this.id,
    required this.time,
    required this.isEnabled,
    required this.state,
    required this.visit,
  });

  const OwnerAvailabilitySlotContent.initial()
    : id = '',
      time = '',
      isEnabled = false,
      state = '',
      visit = null;

  factory OwnerAvailabilitySlotContent.fromJson(Map<String, dynamic> json) {
    return OwnerAvailabilitySlotContent(
      id: json['id'] as String? ?? '',
      time: json['time'] as String? ?? '',
      isEnabled: json['is_enabled'] as bool? ?? false,
      state: json['state'] as String? ?? '',
      visit: json['visit'] is Map
          ? (json['visit'] as Map).cast<String, dynamic>()
          : null,
    );
  }

  final String id;
  final String time;
  final bool isEnabled;
  final String state;
  final Map<String, dynamic>? visit;

  OwnerAvailabilitySlotState get slotState {
    if (state == 'booked' || visit != null) {
      return OwnerAvailabilitySlotState.booked;
    }
    return isEnabled
        ? OwnerAvailabilitySlotState.available
        : OwnerAvailabilitySlotState.unspecified;
  }

  Map<String, dynamic> toJson() => {
    'id': id,
    'time': time,
    'is_enabled': isEnabled,
    'state': state,
    'visit': visit,
  };

  OwnerAvailabilitySlotContent copyWith({
    String? id,
    String? time,
    bool? isEnabled,
    String? state,
    Map<String, dynamic>? visit,
    bool clearVisit = false,
  }) {
    return OwnerAvailabilitySlotContent(
      id: id ?? this.id,
      time: time ?? this.time,
      isEnabled: isEnabled ?? this.isEnabled,
      state: state ?? this.state,
      visit: clearVisit ? null : visit ?? this.visit,
    );
  }

  @override
  List<Object?> get props => [id, time, isEnabled, state, visit];
}

String _ownerAvailabilityDayName(int weekday) {
  return switch (weekday) {
    DateTime.monday => 'monday',
    DateTime.tuesday => 'tuesday',
    DateTime.wednesday => 'wednesday',
    DateTime.thursday => 'thursday',
    DateTime.friday => 'friday',
    DateTime.saturday => 'saturday',
    DateTime.sunday => 'sunday',
    _ => '',
  };
}
