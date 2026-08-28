import 'package:equatable/equatable.dart';

class OwnerDashboardModel extends Equatable {
  const OwnerDashboardModel({
    required this.owner,
    required this.visitsThisWeek,
    required this.activeProperties,
    required this.overallRating,
    required this.pendingRequests,
    required this.pendingVisits,
  });

  const OwnerDashboardModel.initial()
    : owner = const OwnerDashboardOwnerModel.initial(),
      visitsThisWeek = 0,
      activeProperties = 0,
      overallRating = 0,
      pendingRequests = 0,
      pendingVisits = const [];

  factory OwnerDashboardModel.fromJson(Map<String, dynamic> json) {
    final Object? ownerJson = json['owner'];
    return OwnerDashboardModel(
      owner: ownerJson is Map<String, dynamic>
          ? OwnerDashboardOwnerModel.fromJson(ownerJson)
          : const OwnerDashboardOwnerModel.initial(),
      visitsThisWeek: (json['visits_this_week'] as num?)?.toInt() ?? 0,
      activeProperties: (json['active_properties'] as num?)?.toInt() ?? 0,
      overallRating: (json['overall_rating'] as num?)?.toDouble() ?? 0,
      pendingRequests: (json['pending_requests'] as num?)?.toInt() ?? 0,
      pendingVisits:
          (json['pending_visits'] as List?)
              ?.whereType<Map<String, dynamic>>()
              .map(OwnerDashboardPendingVisitModel.fromJson)
              .toList(growable: false) ??
          const [],
    );
  }

  final OwnerDashboardOwnerModel owner;
  final int visitsThisWeek;
  final int activeProperties;
  final double overallRating;
  final int pendingRequests;
  final List<OwnerDashboardPendingVisitModel> pendingVisits;

  @override
  List<Object?> get props => [
    owner,
    visitsThisWeek,
    activeProperties,
    overallRating,
    pendingRequests,
    pendingVisits,
  ];
}

class OwnerDashboardOwnerModel extends Equatable {
  const OwnerDashboardOwnerModel({
    required this.name,
    required this.avatar,
    required this.isVerified,
  });

  const OwnerDashboardOwnerModel.initial()
    : name = '',
      avatar = null,
      isVerified = false;

  factory OwnerDashboardOwnerModel.fromJson(Map<String, dynamic> json) {
    return OwnerDashboardOwnerModel(
      name: json['name'] as String? ?? '',
      avatar: _nullableString(json['avatar']),
      isVerified: json['is_verified'] as bool? ?? false,
    );
  }

  final String name;
  final String? avatar;
  final bool isVerified;

  @override
  List<Object?> get props => [name, avatar, isVerified];
}

class OwnerDashboardPendingVisitModel extends Equatable {
  const OwnerDashboardPendingVisitModel({
    required this.id,
    required this.tenantName,
    required this.tenantAvatar,
    required this.propertyTitle,
    required this.propertyDistrict,
    required this.scheduledAt,
  });

  factory OwnerDashboardPendingVisitModel.fromJson(Map<String, dynamic> json) {
    return OwnerDashboardPendingVisitModel(
      id: json['id'] as String? ?? '',
      tenantName: json['tenant_name'] as String? ?? '',
      tenantAvatar: _nullableString(json['tenant_avatar']),
      propertyTitle: json['property_title'] as String? ?? '',
      propertyDistrict: json['property_district'] as String? ?? '',
      scheduledAt: json['scheduled_at'] as String? ?? '',
    );
  }

  final String id;
  final String tenantName;
  final String? tenantAvatar;
  final String propertyTitle;
  final String propertyDistrict;
  final String scheduledAt;

  @override
  List<Object?> get props => [
    id,
    tenantName,
    tenantAvatar,
    propertyTitle,
    propertyDistrict,
    scheduledAt,
  ];
}

String? _nullableString(Object? value) {
  final String? stringValue = value?.toString().trim();
  return stringValue == null || stringValue.isEmpty ? null : stringValue;
}
