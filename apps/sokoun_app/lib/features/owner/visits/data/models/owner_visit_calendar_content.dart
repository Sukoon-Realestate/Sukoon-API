part of '../../imports.dart';

class OwnerVisitCalendarContent extends Equatable {
  const OwnerVisitCalendarContent({
    required this.year,
    required this.month,
    required this.days,
    required this.selectedDate,
    required this.visits,
  });

  factory OwnerVisitCalendarContent.initial(DateTime date) {
    final DateTime normalizedDate = DateUtils.dateOnly(date);
    return OwnerVisitCalendarContent(
      year: normalizedDate.year,
      month: normalizedDate.month,
      days: const [],
      selectedDate: formatDate(normalizedDate),
      visits: const [],
    );
  }

  factory OwnerVisitCalendarContent.fromJson(
    Map<String, dynamic> json, {
    DateTime? fallbackDate,
  }) {
    final DateTime fallback = DateUtils.dateOnly(
      fallbackDate ?? DateTime.now(),
    );
    final int year = (json['year'] as num?)?.toInt() ?? fallback.year;
    final int month = (json['month'] as num?)?.toInt() ?? fallback.month;
    final String selectedDate =
        json['selected_date'] as String? ??
        formatDate(DateTime(year, month, fallback.day));

    return OwnerVisitCalendarContent(
      year: year,
      month: month,
      days:
          (json['days'] as List?)
              ?.whereType<Map<String, dynamic>>()
              .map(OwnerCalendarDayContent.fromJson)
              .toList(growable: false) ??
          const [],
      selectedDate: selectedDate,
      visits:
          (json['visits'] as List?)
              ?.whereType<Map<String, dynamic>>()
              .map(OwnerCalendarVisitContent.fromJson)
              .toList(growable: false) ??
          const [],
    );
  }

  final int year;
  final int month;
  final List<OwnerCalendarDayContent> days;
  final String selectedDate;
  final List<OwnerCalendarVisitContent> visits;

  DateTime get selectedDateValue =>
      DateTime.tryParse(selectedDate) ?? DateTime(year, month);

  String get firstPropertyId {
    for (final OwnerCalendarVisitContent visit in visits) {
      if (visit.property.id.trim().isNotEmpty) {
        return visit.property.id;
      }
    }
    return '';
  }

  List<int?> get monthDays {
    final DateTime firstDay = DateTime(year, month);
    final int leadingEmptyDays = firstDay.weekday % DateTime.daysPerWeek;
    final int daysInMonth = DateTime(year, month + 1, 0).day;
    final List<int?> cells = <int?>[
      ...List<int?>.filled(leadingEmptyDays, null),
      ...List<int>.generate(daysInMonth, (index) => index + 1),
    ];
    final int trailingEmptyDays =
        (DateTime.daysPerWeek - cells.length % DateTime.daysPerWeek) %
        DateTime.daysPerWeek;
    cells.addAll(List<int?>.filled(trailingEmptyDays, null));
    return cells;
  }

  bool hasVisitsOn(int day) {
    return days.any(
      (calendarDay) => calendarDay.day == day && calendarDay.visitCount > 0,
    );
  }

  Map<String, dynamic> toJson() => {
    'year': year,
    'month': month,
    'days': days.map((day) => day.toJson()).toList(growable: false),
    'selected_date': selectedDate,
    'visits': visits.map((visit) => visit.toJson()).toList(growable: false),
  };

  OwnerVisitCalendarContent copyWith({
    int? year,
    int? month,
    List<OwnerCalendarDayContent>? days,
    String? selectedDate,
    List<OwnerCalendarVisitContent>? visits,
  }) {
    return OwnerVisitCalendarContent(
      year: year ?? this.year,
      month: month ?? this.month,
      days: days ?? this.days,
      selectedDate: selectedDate ?? this.selectedDate,
      visits: visits ?? this.visits,
    );
  }

  static String formatDate(DateTime date) {
    final String month = date.month.toString().padLeft(2, '0');
    final String day = date.day.toString().padLeft(2, '0');
    return '${date.year}-$month-$day';
  }

  static List<String> get weekdayHeaders => [
    LocaleKeys.ownerCalendarDaySundayShort,
    LocaleKeys.ownerCalendarDayMondayShort,
    LocaleKeys.ownerCalendarDayTuesdayShort,
    LocaleKeys.ownerCalendarDayWednesdayShort,
    LocaleKeys.ownerCalendarDayThursdayShort,
    LocaleKeys.ownerCalendarDayFridayShort,
    LocaleKeys.ownerCalendarDaySaturdayShort,
  ];

  @override
  List<Object?> get props => [year, month, days, selectedDate, visits];
}

class OwnerCalendarDayContent extends Equatable {
  const OwnerCalendarDayContent({
    required this.date,
    required this.day,
    required this.visitCount,
  });

  const OwnerCalendarDayContent.initial() : date = '', day = 0, visitCount = 0;

  factory OwnerCalendarDayContent.fromJson(Map<String, dynamic> json) {
    return OwnerCalendarDayContent(
      date: json['date'] as String? ?? '',
      day: (json['day'] as num?)?.toInt() ?? 0,
      visitCount: (json['visit_count'] as num?)?.toInt() ?? 0,
    );
  }

  final String date;
  final int day;
  final int visitCount;

  Map<String, dynamic> toJson() => {
    'date': date,
    'day': day,
    'visit_count': visitCount,
  };

  OwnerCalendarDayContent copyWith({String? date, int? day, int? visitCount}) {
    return OwnerCalendarDayContent(
      date: date ?? this.date,
      day: day ?? this.day,
      visitCount: visitCount ?? this.visitCount,
    );
  }

  @override
  List<Object?> get props => [date, day, visitCount];
}

class OwnerCalendarVisitContent extends Equatable {
  const OwnerCalendarVisitContent({
    required this.id,
    required this.tenant,
    required this.property,
    required this.visitTime,
    required this.status,
  });

  const OwnerCalendarVisitContent.initial()
    : id = '',
      tenant = const OwnerCalendarTenantContent.initial(),
      property = const OwnerCalendarPropertyContent.initial(),
      visitTime = '',
      status = OwnerVisitRequestStatus.pending;

  factory OwnerCalendarVisitContent.fromJson(Map<String, dynamic> json) {
    return OwnerCalendarVisitContent(
      id: json['id'] as String? ?? '',
      tenant: OwnerCalendarTenantContent.fromJson(
        _ownerVisitJsonMap(json['tenant']),
      ),
      property: OwnerCalendarPropertyContent.fromJson(
        _ownerVisitJsonMap(json['property']),
      ),
      visitTime: json['visit_time'] as String? ?? '',
      status: OwnerVisitRequestStatusExtension.fromName(
        json['status'] as String?,
      ),
    );
  }

  final String id;
  final OwnerCalendarTenantContent tenant;
  final OwnerCalendarPropertyContent property;
  final String visitTime;
  final OwnerVisitRequestStatus status;

  String get tenantInitial {
    final String name = tenant.name.trim();
    return name.isEmpty ? '' : name.substring(0, 1);
  }

  Map<String, dynamic> toJson() => {
    'id': id,
    'tenant': tenant.toJson(),
    'property': property.toJson(),
    'visit_time': visitTime,
    'status': status.name,
  };

  OwnerCalendarVisitContent copyWith({
    String? id,
    OwnerCalendarTenantContent? tenant,
    OwnerCalendarPropertyContent? property,
    String? visitTime,
    OwnerVisitRequestStatus? status,
  }) {
    return OwnerCalendarVisitContent(
      id: id ?? this.id,
      tenant: tenant ?? this.tenant,
      property: property ?? this.property,
      visitTime: visitTime ?? this.visitTime,
      status: status ?? this.status,
    );
  }

  @override
  List<Object?> get props => [id, tenant, property, visitTime, status];
}

class OwnerCalendarTenantContent extends Equatable {
  const OwnerCalendarTenantContent({required this.id, required this.name});

  const OwnerCalendarTenantContent.initial() : id = '', name = '';

  factory OwnerCalendarTenantContent.fromJson(Map<String, dynamic> json) {
    return OwnerCalendarTenantContent(
      id: json['id'] as String? ?? '',
      name: json['name'] as String? ?? '',
    );
  }

  final String id;
  final String name;

  Map<String, dynamic> toJson() => {'id': id, 'name': name};

  OwnerCalendarTenantContent copyWith({String? id, String? name}) {
    return OwnerCalendarTenantContent(
      id: id ?? this.id,
      name: name ?? this.name,
    );
  }

  @override
  List<Object?> get props => [id, name];
}

class OwnerCalendarPropertyContent extends Equatable {
  const OwnerCalendarPropertyContent({required this.id, required this.title});

  const OwnerCalendarPropertyContent.initial() : id = '', title = '';

  factory OwnerCalendarPropertyContent.fromJson(Map<String, dynamic> json) {
    return OwnerCalendarPropertyContent(
      id: json['id'] as String? ?? '',
      title: json['title'] as String? ?? '',
    );
  }

  final String id;
  final String title;

  Map<String, dynamic> toJson() => {'id': id, 'title': title};

  OwnerCalendarPropertyContent copyWith({String? id, String? title}) {
    return OwnerCalendarPropertyContent(
      id: id ?? this.id,
      title: title ?? this.title,
    );
  }

  @override
  List<Object?> get props => [id, title];
}

Map<String, dynamic> _ownerVisitJsonMap(Object? value) {
  return value is Map ? value.cast<String, dynamic>() : const {};
}
