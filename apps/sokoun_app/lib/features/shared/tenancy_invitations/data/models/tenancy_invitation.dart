import 'package:equatable/equatable.dart';
import 'package:sokoun_app/features/main_view/data/enums/app_workspace.dart';
import 'package:sokoun_app/features/shared/premium/data/premium_json.dart';
import 'package:sokoun_app/features/shared/rental_offers/data/models/rental_selection.dart';

import '../enums/tenancy_invitation_status.dart';

class TenancyInvitation extends Equatable {
  const TenancyInvitation({
    this.id = '',
    this.propertyId = '',
    this.propertyTitle = '',
    this.ownerId = '',
    this.ownerName = '',
    this.tenantId = '',
    this.tenantName = '',
    this.offerId = '',
    this.rentalSelection,
    this.status = TenancyInvitationStatus.unknown,
    this.revision = 0,
    this.createdAt,
    this.expiresAt,
    this.acceptedAt,
    this.leaseId = '',
    this.eligibleForLease = false,
    this.canRespond = false,
  });
  const TenancyInvitation.initial() : this();

  factory TenancyInvitation.fromJson(Map<String, dynamic> json) =>
      TenancyInvitation(
        id: premiumString(json['id']),
        propertyId: premiumString(json['property_id']),
        propertyTitle: premiumString(json['property_title']),
        ownerId: premiumString(json['owner_id']),
        ownerName: premiumString(json['owner_name']),
        tenantId: premiumString(json['tenant_id']),
        tenantName: premiumString(json['tenant_name']),
        offerId: premiumString(json['offer_id']),
        rentalSelection:
            premiumString(json['offer_id']).isNotEmpty ||
                premiumMap(json['offer_snapshot']).isNotEmpty
            ? RentalSelection.fromRecord(json)
            : null,
        status: TenancyInvitationStatus.fromJson(json['status']),
        revision: premiumInt(json['revision']) ?? 0,
        createdAt: premiumDate(json['created_at']),
        expiresAt: premiumDate(json['expires_at']),
        acceptedAt: premiumDate(json['accepted_at']),
        leaseId: premiumString(json['lease_id']),
        eligibleForLease: json['eligible_for_lease'] == true,
        canRespond: premiumMap(json['actions'])['can_respond'] == true,
      );

  final String id, propertyId, propertyTitle, ownerId, ownerName;
  final String tenantId, tenantName, offerId, leaseId;
  final RentalSelection? rentalSelection;
  final TenancyInvitationStatus status;
  final int revision;
  final DateTime? createdAt, expiresAt, acceptedAt;
  final bool eligibleForLease, canRespond;

  bool get hasValidIdentity =>
      id.isNotEmpty &&
      propertyId.isNotEmpty &&
      ownerId.isNotEmpty &&
      tenantId.isNotEmpty &&
      ownerId != tenantId &&
      revision > 0 &&
      status != TenancyInvitationStatus.unknown &&
      (!eligibleForLease || status == TenancyInvitationStatus.accepted) &&
      createdAt != null &&
      expiresAt != null &&
      expiresAt!.isAfter(createdAt!) &&
      (offerId.isEmpty
          ? rentalSelection == null
          : rentalSelection?.canIdentify == true &&
                rentalSelection?.propertyId == propertyId &&
                rentalSelection?.offerId == offerId &&
                rentalSelection!.offerRevision > 0);

  bool belongsTo(String accountId, AppWorkspace workspace) =>
      accountId.isNotEmpty &&
      (workspace.isOwner ? ownerId : tenantId) == accountId;

  bool get isExpired =>
      expiresAt == null || !expiresAt!.isAfter(DateTime.now());

  bool canRespondAs(String accountId) =>
      hasValidIdentity &&
      accountId.isNotEmpty &&
      tenantId == accountId &&
      status == TenancyInvitationStatus.pending &&
      canRespond &&
      leaseId.isEmpty &&
      !isExpired;

  bool get isEligible =>
      hasValidIdentity &&
      status == TenancyInvitationStatus.accepted &&
      eligibleForLease &&
      leaseId.isEmpty &&
      !isExpired;

  Map<String, dynamic> toJson() => {
    'id': id,
    'property_id': propertyId,
    'property_title': propertyTitle,
    'owner_id': ownerId,
    'owner_name': ownerName,
    'tenant_id': tenantId,
    'tenant_name': tenantName,
    if (offerId.isNotEmpty) 'offer_id': offerId,
    if (rentalSelection != null) 'offer_snapshot': rentalSelection!.toJson(),
    'status': status.name,
    'revision': revision,
    'created_at': createdAt?.toIso8601String(),
    'expires_at': expiresAt?.toIso8601String(),
    'accepted_at': acceptedAt?.toIso8601String(),
    'lease_id': leaseId,
    'eligible_for_lease': eligibleForLease,
    'actions': {'can_respond': canRespond},
  };

  TenancyInvitation copyWith({
    TenancyInvitationStatus? status,
    int? revision,
    bool? eligibleForLease,
    bool? canRespond,
    DateTime? expiresAt,
    String? leaseId,
  }) => TenancyInvitation(
    id: id,
    propertyId: propertyId,
    propertyTitle: propertyTitle,
    ownerId: ownerId,
    ownerName: ownerName,
    tenantId: tenantId,
    tenantName: tenantName,
    offerId: offerId,
    rentalSelection: rentalSelection,
    status: status ?? this.status,
    revision: revision ?? this.revision,
    createdAt: createdAt,
    expiresAt: expiresAt ?? this.expiresAt,
    acceptedAt: acceptedAt,
    leaseId: leaseId ?? this.leaseId,
    eligibleForLease: eligibleForLease ?? this.eligibleForLease,
    canRespond: canRespond ?? this.canRespond,
  );

  @override
  List<Object?> get props => [
    id,
    propertyId,
    propertyTitle,
    ownerId,
    ownerName,
    tenantId,
    tenantName,
    offerId,
    rentalSelection,
    status,
    revision,
    createdAt,
    expiresAt,
    acceptedAt,
    leaseId,
    eligibleForLease,
    canRespond,
  ];
}
