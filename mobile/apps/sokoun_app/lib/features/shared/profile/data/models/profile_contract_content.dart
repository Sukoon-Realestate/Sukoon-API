import 'package:equatable/equatable.dart';
import '../profile_json.dart';

class ProfileContractContent extends Equatable {
  const ProfileContractContent({
    required this.id,
    required this.propertyTitle,
    required this.status,
    required this.startDate,
    required this.endDate,
    required this.documentUrl,
  });
  const ProfileContractContent.initial()
    : id = '',
      propertyTitle = '',
      status = '',
      startDate = '',
      endDate = '',
      documentUrl = '';
  factory ProfileContractContent.fromJson(Map<String, dynamic> json) =>
      ProfileContractContent(
        id: profileString(json['id']),
        propertyTitle: profileString(json['property_title']),
        status: profileString(json['status']),
        startDate: profileString(json['start_date']),
        endDate: profileString(json['end_date']),
        documentUrl: profileString(json['document_url']),
      );
  final String id;
  final String propertyTitle;
  final String status;
  final String startDate;
  final String endDate;
  final String documentUrl;
  Map<String, dynamic> toJson() => {
    'id': id,
    'property_title': propertyTitle,
    'status': status,
    'start_date': startDate,
    'end_date': endDate,
    'document_url': documentUrl,
  };
  ProfileContractContent copyWith({
    String? id,
    String? propertyTitle,
    String? status,
    String? startDate,
    String? endDate,
    String? documentUrl,
  }) => ProfileContractContent(
    id: id ?? this.id,
    propertyTitle: propertyTitle ?? this.propertyTitle,
    status: status ?? this.status,
    startDate: startDate ?? this.startDate,
    endDate: endDate ?? this.endDate,
    documentUrl: documentUrl ?? this.documentUrl,
  );
  @override
  List<Object?> get props => [
    id,
    propertyTitle,
    status,
    startDate,
    endDate,
    documentUrl,
  ];
}
