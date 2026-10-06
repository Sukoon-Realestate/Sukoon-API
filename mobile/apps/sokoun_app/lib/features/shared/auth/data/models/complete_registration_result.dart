import 'package:equatable/equatable.dart';

class CompleteRegistrationResult extends Equatable {
  const CompleteRegistrationResult({
    required this.registrationComplete,
    required this.verificationStatus,
    required this.missingFields,
  });
  const CompleteRegistrationResult.initial()
    : registrationComplete = false,
      verificationStatus = '',
      missingFields = const [];

  factory CompleteRegistrationResult.fromJson(Map<String, dynamic> json) =>
      CompleteRegistrationResult(
        registrationComplete: json['registration_complete'] ?? false,
        verificationStatus: json['verification_status']?.toString() ?? '',
        missingFields: (json['missing_fields'] as List? ?? const [])
            .map((field) => field.toString())
            .toList(growable: false),
      );

  final bool registrationComplete;
  final String verificationStatus;
  final List<String> missingFields;
  bool get isComplete => registrationComplete && missingFields.isEmpty;

  Map<String, dynamic> toJson() => {
    'registration_complete': registrationComplete,
    'verification_status': verificationStatus,
    'missing_fields': missingFields,
  };
  CompleteRegistrationResult copyWith({
    bool? registrationComplete,
    String? verificationStatus,
    List<String>? missingFields,
  }) => CompleteRegistrationResult(
    registrationComplete: registrationComplete ?? this.registrationComplete,
    verificationStatus: verificationStatus ?? this.verificationStatus,
    missingFields: missingFields ?? this.missingFields,
  );
  @override
  List<Object?> get props => [
    registrationComplete,
    verificationStatus,
    missingFields,
  ];
}
