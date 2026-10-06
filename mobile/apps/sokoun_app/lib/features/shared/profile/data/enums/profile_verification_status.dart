enum ProfileVerificationStatus {
  incomplete,
  pending,
  approved,
  rejected,
  unknown;

  bool get isApproved => this == approved;
  bool get isPending => this == pending;
  bool get isRejected => this == rejected;
  bool get canSubmit => this == incomplete || this == rejected;
}
