import 'package:equatable/equatable.dart';
import '../profile_json.dart';
import '../enums/profile_verification_status.dart';

class ProfileVerificationContent extends Equatable {
  const ProfileVerificationContent({
    required this.status,
    required this.fullName,
    required this.submittedAt,
    required this.rejectionReason,
  });
  const ProfileVerificationContent.initial()
    : status = ProfileVerificationStatus.unknown,
      fullName = '',
      submittedAt = '',
      rejectionReason = '';
  factory ProfileVerificationContent.fromJson(Map<String, dynamic> json) =>
      ProfileVerificationContent(
        status: ProfileVerificationStatus.values.firstWhere(
          (value) => value.name == json['status'],
          orElse: () => ProfileVerificationStatus.unknown,
        ),
        fullName: profileString(json['full_name']),
        submittedAt: profileString(json['submitted_at']),
        rejectionReason: profileString(json['rejection_reason']),
      );
  final ProfileVerificationStatus status;
  final String fullName;
  final String submittedAt;
  final String rejectionReason;
  Map<String, dynamic> toJson() => {
    'status': status.name,
    'full_name': fullName,
    'submitted_at': submittedAt,
    'rejection_reason': rejectionReason,
  };
  ProfileVerificationContent copyWith({
    ProfileVerificationStatus? status,
    String? fullName,
    String? submittedAt,
    String? rejectionReason,
  }) => ProfileVerificationContent(
    status: status ?? this.status,
    fullName: fullName ?? this.fullName,
    submittedAt: submittedAt ?? this.submittedAt,
    rejectionReason: rejectionReason ?? this.rejectionReason,
  );
  @override
  List<Object?> get props => [status, fullName, submittedAt, rejectionReason];
}
