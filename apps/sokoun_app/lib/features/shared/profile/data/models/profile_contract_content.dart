import 'package:sokoun_app/features/shared/rental_offers/data/models/rental_selection.dart';
import 'package:equatable/equatable.dart';
import '../profile_json.dart';

class ProfileContractContent extends Equatable {
  const ProfileContractContent({
    this.rentalSelection,
    required this.id,
    required this.propertyTitle,
    required this.status,
    required this.startDate,
    required this.endDate,
    required this.documentUrl,
    this.leaseId = '',
  });
  const ProfileContractContent.initial()
    : rentalSelection = null,
      id = '',
      propertyTitle = '',
      status = '',
      startDate = '',
      endDate = '',
      leaseId = '',
      documentUrl = '';
  factory ProfileContractContent.fromJson(Map<String, dynamic> json) =>
      ProfileContractContent(
        rentalSelection: RentalSelection.fromRecord(json),
        id: profileString(json['id']),
        propertyTitle: profileString(json['property_title']),
        status: profileString(json['status']),
        startDate: profileString(json['start_date']),
        endDate: profileString(json['end_date']),
        documentUrl: profileString(json['document_url']),
        leaseId: profileString(json['lease_id']),
      );
  final RentalSelection? rentalSelection;
  final String id;
  final String propertyTitle;
  final String status;
  final String startDate;
  final String endDate;
  final String documentUrl;
  final String leaseId;
  Map<String, dynamic> toJson() => {
    'id': id,
    if (rentalSelection != null) ...{
      'offer_id': rentalSelection!.offerId,
      'offer_snapshot': rentalSelection!.toJson(),
    },
    'property_title': propertyTitle,
    'status': status,
    'start_date': startDate,
    'end_date': endDate,
    'document_url': documentUrl,
    if (leaseId.isNotEmpty) 'lease_id': leaseId,
  };
  ProfileContractContent copyWith({
    RentalSelection? rentalSelection,
    String? id,
    String? propertyTitle,
    String? status,
    String? startDate,
    String? endDate,
    String? documentUrl,
    String? leaseId,
  }) => ProfileContractContent(
    rentalSelection: rentalSelection ?? this.rentalSelection,
    id: id ?? this.id,
    propertyTitle: propertyTitle ?? this.propertyTitle,
    status: status ?? this.status,
    startDate: startDate ?? this.startDate,
    endDate: endDate ?? this.endDate,
    documentUrl: documentUrl ?? this.documentUrl,
    leaseId: leaseId ?? this.leaseId,
  );
  @override
  List<Object?> get props => [
    rentalSelection,
    id,
    propertyTitle,
    status,
    startDate,
    endDate,
    documentUrl,
    leaseId,
  ];
}
