import 'package:equatable/equatable.dart';
import 'package:sokoun_app/features/shared/premium/data/premium_json.dart';

class CreateTenancyInvitationBody extends Equatable {
  const CreateTenancyInvitationBody({
    this.propertyId = '',
    this.tenantId = '',
    this.offerId = '',
    this.expectedOfferRevision = 0,
    this.requestKey = '',
  });
  const CreateTenancyInvitationBody.initial() : this();

  factory CreateTenancyInvitationBody.fromJson(Map<String, dynamic> json) =>
      CreateTenancyInvitationBody(
        propertyId: premiumString(json['property_id']),
        tenantId: premiumString(json['tenant_id']),
        offerId: premiumString(json['offer_id']),
        expectedOfferRevision: premiumInt(json['expected_offer_revision']) ?? 0,
        requestKey: premiumString(json['request_key']),
      );

  final String propertyId, tenantId, offerId, requestKey;
  final int expectedOfferRevision;

  bool get isValid =>
      propertyId.isNotEmpty &&
      tenantId.isNotEmpty &&
      requestKey.isNotEmpty &&
      (offerId.isEmpty
          ? expectedOfferRevision == 0
          : expectedOfferRevision > 0);

  Map<String, dynamic> toJson() => {
    'property_id': propertyId,
    'tenant_id': tenantId,
    if (offerId.isNotEmpty) ...{
      'offer_id': offerId,
      'expected_offer_revision': expectedOfferRevision,
    },
    'request_key': requestKey,
  };

  @override
  List<Object?> get props => [
    propertyId,
    tenantId,
    offerId,
    expectedOfferRevision,
    requestKey,
  ];
}
