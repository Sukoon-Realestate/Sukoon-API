import 'package:equatable/equatable.dart';
import 'package:sokoun_app/features/shared/premium/data/premium_json.dart';
import 'package:sokoun_app/features/shared/premium/data/enums/premium_status.dart';
import 'package:sokoun_app/features/shared/premium/data/models/premium_money.dart';

class DigitalLease extends Equatable {
  const DigitalLease({
    this.id = '',
    this.propertyId = '',
    this.propertyTitle = '',
    this.ownerName = '',
    this.tenantName = '',
    this.startDate,
    this.endDate,
    this.rent = const PremiumMoney.initial(),
    this.status = PremiumStatus.unknown,
    this.revision = 0,
    this.documentUrl = '',
    this.canSign = false,
    this.canCancel = false,
  });
  const DigitalLease.initial() : this();
  factory DigitalLease.fromJson(Map<String, dynamic> json) => DigitalLease(
    id: premiumString(json['id']),
    propertyId: premiumString(json['property_id']),
    propertyTitle: premiumString(json['property_title']),
    ownerName: premiumString(json['owner_name']),
    tenantName: premiumString(json['tenant_name']),
    startDate: premiumDate(json['start_date']),
    endDate: premiumDate(json['end_date']),
    rent: PremiumMoney.fromJson(premiumMap(json['rent'])),
    status: PremiumStatus.fromValue(json['status']),
    revision: premiumInt(json['revision']) ?? 0,
    documentUrl: premiumString(json['document_url']),
    canSign: json['can_sign'] == true,
    canCancel: json['can_cancel'] == true,
  );
  final String id;
  final String propertyId;
  final String propertyTitle;
  final String ownerName;
  final String tenantName;
  final DateTime? startDate;
  final DateTime? endDate;
  final PremiumMoney rent;
  final PremiumStatus status;
  final int revision;
  final String documentUrl;
  final bool canSign;
  final bool canCancel;

  Map<String, dynamic> toJson() => {
    'id': id,
    'property_id': propertyId,
    'property_title': propertyTitle,
    'owner_name': ownerName,
    'tenant_name': tenantName,
    'start_date': startDate?.toIso8601String(),
    'end_date': endDate?.toIso8601String(),
    'rent': rent.toJson(),
    'status': status.name,
    'revision': revision,
    'document_url': documentUrl,
    'can_sign': canSign,
    'can_cancel': canCancel,
  };
  DigitalLease copyWith({
    String? id,
    String? propertyId,
    String? propertyTitle,
    String? ownerName,
    String? tenantName,
    DateTime? startDate,
    DateTime? endDate,
    PremiumMoney? rent,
    PremiumStatus? status,
    int? revision,
    String? documentUrl,
    bool? canSign,
    bool? canCancel,
  }) => DigitalLease(
    id: id ?? this.id,
    propertyId: propertyId ?? this.propertyId,
    propertyTitle: propertyTitle ?? this.propertyTitle,
    ownerName: ownerName ?? this.ownerName,
    tenantName: tenantName ?? this.tenantName,
    startDate: startDate ?? this.startDate,
    endDate: endDate ?? this.endDate,
    rent: rent ?? this.rent,
    status: status ?? this.status,
    revision: revision ?? this.revision,
    documentUrl: documentUrl ?? this.documentUrl,
    canSign: canSign ?? this.canSign,
    canCancel: canCancel ?? this.canCancel,
  );
  @override
  List<Object?> get props => [
    id,
    propertyId,
    propertyTitle,
    ownerName,
    tenantName,
    startDate,
    endDate,
    rent,
    status,
    revision,
    documentUrl,
    canSign,
    canCancel,
  ];
}
