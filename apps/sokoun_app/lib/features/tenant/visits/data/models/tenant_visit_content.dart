part of '../../imports.dart';

class TenantVisitContent extends Equatable {
  const TenantVisitContent({
    required this.id,
    required this.propertyTitle,
    required this.day,
    required this.time,
    required this.status,
    required this.statusText,
    this.ownerName = '',
    this.ownerPhone = '',
    this.ownerId = '',
    this.actions,
  });

  const TenantVisitContent.initial()
    : id = '',
      propertyTitle = '',
      day = '',
      time = '',
      status = TenantVisitStatus.pending,
      statusText = '',
      ownerName = '',
      ownerPhone = '',
      ownerId = '',
      actions = null;

  factory TenantVisitContent.fromJson(Map<String, dynamic> json) {
    final String statusText =
        (json['status_label'] ?? json['status'])?.toString() ?? '';
    final Map<String, dynamic> property = _visitMap(json['property']);
    final Object? ownerValue = json['owner'];
    final Map<String, dynamic> owner = ownerValue is Map
        ? Map<String, dynamic>.from(ownerValue)
        : const {};
    return TenantVisitContent(
      id: json['id'] as String? ?? '',
      propertyTitle:
          property['title']?.toString() ??
          json['title'] as String? ??
          json['property_title'] as String? ??
          '',
      day:
          json['day_label'] as String? ??
          json['day'] as String? ??
          json['detail_date'] as String? ??
          json['date_label'] as String? ??
          json['visit_date'] as String? ??
          '',
      time:
          (json['time_label'] ?? json['visit_time'] ?? json['time'])
              ?.toString() ??
          '',
      status: TenantVisitStatusX.fromApiValue(
        json['status']?.toString() ?? statusText,
      ),
      statusText: statusText,
      ownerName:
          json['owner_name']?.toString() ??
          owner['full_name']?.toString() ??
          owner['name']?.toString() ??
          '',
      ownerPhone:
          json['owner_phone']?.toString() ??
          owner['phone_number']?.toString() ??
          owner['phone']?.toString() ??
          '',
      ownerId: json['owner_id']?.toString() ?? owner['id']?.toString() ?? '',
      actions: json['actions'] is Map
          ? VisitActions.fromJson(_visitMap(json['actions']))
          : null,
    );
  }

  final String id;
  final String propertyTitle;
  final String day;
  final String time;
  final TenantVisitStatus status;
  final String statusText;
  final String ownerName;
  final String ownerPhone;
  final String ownerId;
  final VisitActions? actions;

  bool get canCancel =>
      actions?.canCancel ?? (status.isPending || status.isAccepted);
  bool get canChat =>
      (actions?.canChat ?? status.isAccepted) && ownerId.isNotEmpty;
  bool get canReview =>
      actions?.canReview ?? (status.isAccepted || status.isCompleted);
  bool get canFindAlternative =>
      actions?.canFindAlternative ?? status.isRejected;

  String get dateLabel =>
      [day, time].where((value) => value.trim().isNotEmpty).join(' · ');

  String get detailDate => day;

  String get resolvedStatusText =>
      statusText.trim().isEmpty ? status.label : statusText;

  Map<String, dynamic> toJson() => {
    'id': id,
    'title': propertyTitle,
    'day': day,
    'time': time,
    'status': status.name,
    'status_label': statusText,
    if (actions != null) 'actions': actions!.toJson(),
    'owner_name': ownerName,
    'owner_phone': ownerPhone,
    'owner_id': ownerId,
  };

  TenantVisitContent copyWith({
    String? id,
    String? propertyTitle,
    String? day,
    String? time,
    TenantVisitStatus? status,
    String? statusText,
    String? ownerName,
    String? ownerPhone,
    String? ownerId,
    VisitActions? actions,
  }) {
    return TenantVisitContent(
      id: id ?? this.id,
      propertyTitle: propertyTitle ?? this.propertyTitle,
      day: day ?? this.day,
      time: time ?? this.time,
      status: status ?? this.status,
      statusText: statusText ?? this.statusText,
      ownerName: ownerName ?? this.ownerName,
      ownerPhone: ownerPhone ?? this.ownerPhone,
      ownerId: ownerId ?? this.ownerId,
      actions: actions ?? this.actions,
    );
  }

  @override
  List<Object?> get props => [
    id,
    propertyTitle,
    day,
    time,
    status,
    statusText,
    ownerName,
    ownerPhone,
    ownerId,
    actions,
  ];
}
