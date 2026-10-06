import 'package:equatable/equatable.dart';
import 'package:sokoun_app/features/shared/premium/data/premium_json.dart';
import 'package:sokoun_app/features/tenant/home/data/models/property_search_model.dart';

class PremiumSearchAlert extends Equatable {
  const PremiumSearchAlert({
    this.id = '',
    this.name = '',
    this.cadence = '',
    this.enabled = false,
    this.canManage = false,
    this.revision = 0,
    this.lastMatchedAt,
    this.filters = const PropertySearchFilters.initial(),
  });
  const PremiumSearchAlert.initial() : this();
  factory PremiumSearchAlert.fromJson(Map<String, dynamic> json) =>
      PremiumSearchAlert(
        id: premiumString(json['id']),
        name: premiumString(json['name']),
        cadence: premiumString(json['cadence']),
        enabled: json['enabled'] == true,
        canManage: json['can_manage'] == true,
        revision: premiumInt(json['revision']) ?? 0,
        lastMatchedAt: premiumDate(json['last_matched_at']),
        filters: PropertySearchFilters.fromJson(premiumMap(json['filters'])),
      );
  final String id;
  final String name;
  final String cadence;
  final bool enabled;
  final bool canManage;
  final int revision;
  final DateTime? lastMatchedAt;
  final PropertySearchFilters filters;

  Map<String, dynamic> toJson() => {
    'id': id,
    'name': name,
    'cadence': cadence,
    'enabled': enabled,
    'can_manage': canManage,
    'revision': revision,
    'last_matched_at': lastMatchedAt?.toIso8601String(),
    'filters': filters.toJson(),
  };
  PremiumSearchAlert copyWith({
    String? id,
    String? name,
    String? cadence,
    bool? enabled,
    bool? canManage,
    int? revision,
    DateTime? lastMatchedAt,
    PropertySearchFilters? filters,
  }) => PremiumSearchAlert(
    id: id ?? this.id,
    name: name ?? this.name,
    cadence: cadence ?? this.cadence,
    enabled: enabled ?? this.enabled,
    canManage: canManage ?? this.canManage,
    revision: revision ?? this.revision,
    lastMatchedAt: lastMatchedAt ?? this.lastMatchedAt,
    filters: filters ?? this.filters,
  );
  @override
  List<Object?> get props => [
    id,
    name,
    cadence,
    enabled,
    canManage,
    revision,
    lastMatchedAt,
    filters,
  ];
}
