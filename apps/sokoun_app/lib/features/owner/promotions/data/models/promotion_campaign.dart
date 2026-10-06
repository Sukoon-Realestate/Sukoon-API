import 'package:equatable/equatable.dart';
import 'package:sokoun_app/features/shared/premium/data/premium_json.dart';
import 'package:sokoun_app/features/shared/premium/data/enums/premium_status.dart';

class PromotionCampaign extends Equatable {
  const PromotionCampaign({
    this.id = '',
    this.propertyId = '',
    this.propertyTitle = '',
    this.status = PremiumStatus.unknown,
    this.durationDays = 0,
    this.startsAt,
    this.endsAt,
    this.impressions,
  });
  const PromotionCampaign.initial() : this();
  factory PromotionCampaign.fromJson(Map<String, dynamic> json) =>
      PromotionCampaign(
        id: premiumString(json['id']),
        propertyId: premiumString(json['property_id']),
        propertyTitle: premiumString(json['property_title']),
        status: PremiumStatus.fromValue(json['status']),
        durationDays: premiumInt(json['duration_days']) ?? 0,
        startsAt: premiumDate(json['starts_at']),
        endsAt: premiumDate(json['ends_at']),
        impressions: premiumInt(json['impressions']),
      );
  final String id;
  final String propertyId;
  final String propertyTitle;
  final PremiumStatus status;
  final int durationDays;
  final DateTime? startsAt;
  final DateTime? endsAt;
  final int? impressions;

  Map<String, dynamic> toJson() => {
    'id': id,
    'property_id': propertyId,
    'property_title': propertyTitle,
    'status': status.name,
    'duration_days': durationDays,
    'starts_at': startsAt?.toIso8601String(),
    'ends_at': endsAt?.toIso8601String(),
    'impressions': impressions,
  };
  PromotionCampaign copyWith({
    String? id,
    String? propertyId,
    String? propertyTitle,
    PremiumStatus? status,
    int? durationDays,
    DateTime? startsAt,
    DateTime? endsAt,
    int? impressions,
  }) => PromotionCampaign(
    id: id ?? this.id,
    propertyId: propertyId ?? this.propertyId,
    propertyTitle: propertyTitle ?? this.propertyTitle,
    status: status ?? this.status,
    durationDays: durationDays ?? this.durationDays,
    startsAt: startsAt ?? this.startsAt,
    endsAt: endsAt ?? this.endsAt,
    impressions: impressions ?? this.impressions,
  );
  @override
  List<Object?> get props => [
    id,
    propertyId,
    propertyTitle,
    status,
    durationDays,
    startsAt,
    endsAt,
    impressions,
  ];
}
