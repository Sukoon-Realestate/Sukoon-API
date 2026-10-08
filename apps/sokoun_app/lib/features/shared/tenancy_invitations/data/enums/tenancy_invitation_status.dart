enum TenancyInvitationStatus {
  pending,
  accepted,
  rejected,
  revoked,
  expired,
  unknown;

  static TenancyInvitationStatus fromJson(Object? value) => values.firstWhere(
    (status) => status.name == value,
    orElse: () => unknown,
  );
}
