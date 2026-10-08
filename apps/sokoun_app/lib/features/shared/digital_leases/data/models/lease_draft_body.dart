import 'package:equatable/equatable.dart';
import 'package:sokoun_app/features/shared/rental_offers/data/models/rental_selection.dart';
import 'package:sokoun_app/features/shared/premium/data/premium_json.dart';
import 'package:sokoun_app/features/shared/premium/data/models/premium_money.dart';

class LeaseDraftBody extends Equatable {
  const LeaseDraftBody({
    this.hasRentalOffers = false,
    this.offerId = '',
    this.rentalSelection,
    this.propertyId = '',
    this.tenantId = '',
    this.templateId = '',
    this.templateVersion = '',
    this.startDate = '',
    this.endDate = '',
    this.rent = const PremiumMoney.initial(),
    this.requestKey = '',
  });
  const LeaseDraftBody.initial() : this();
  factory LeaseDraftBody.fromJson(Map<String, dynamic> json) => LeaseDraftBody(
    propertyId: premiumString(json['property_id']),
    offerId: premiumString(json['offer_id']),
    tenantId: premiumString(json['tenant_id']),
    templateId: premiumString(json['template_id']),
    templateVersion: premiumString(json['template_version']),
    startDate: premiumString(json['start_date']),
    endDate: premiumString(json['end_date']),
    rent: PremiumMoney.fromJson(premiumMap(json['rent'])),
    requestKey: premiumString(json['request_key']),
  );
  final bool hasRentalOffers;
  final String offerId;
  final RentalSelection? rentalSelection;
  final String propertyId;
  final String tenantId;
  final String templateId;
  final String templateVersion;
  final String startDate;
  final String endDate;
  final PremiumMoney rent;
  final String requestKey;

  Map<String, dynamic> toJson() => {
    'property_id': propertyId,
    if (offerId.isNotEmpty) 'offer_id': offerId,
    'tenant_id': tenantId,
    'template_id': templateId,
    'template_version': templateVersion,
    'start_date': startDate,
    'end_date': endDate,
    'rent': rent.toJson(),
    'request_key': requestKey,
  };
  LeaseDraftBody copyWith({
    bool? hasRentalOffers,
    String? offerId,
    RentalSelection? rentalSelection,
    String? propertyId,
    String? tenantId,
    String? templateId,
    String? templateVersion,
    String? startDate,
    String? endDate,
    PremiumMoney? rent,
    String? requestKey,
  }) => LeaseDraftBody(
    hasRentalOffers: hasRentalOffers ?? this.hasRentalOffers,
    offerId: offerId ?? this.offerId,
    rentalSelection: rentalSelection ?? this.rentalSelection,
    propertyId: propertyId ?? this.propertyId,
    tenantId: tenantId ?? this.tenantId,
    templateId: templateId ?? this.templateId,
    templateVersion: templateVersion ?? this.templateVersion,
    startDate: startDate ?? this.startDate,
    endDate: endDate ?? this.endDate,
    rent: rent ?? this.rent,
    requestKey: requestKey ?? this.requestKey,
  );
  @override
  List<Object?> get props => [
    hasRentalOffers,
    offerId,
    rentalSelection,
    propertyId,
    tenantId,
    templateId,
    templateVersion,
    startDate,
    endDate,
    rent,
    requestKey,
  ];
}
