enum OwnerPropertyStatus {
  verified,
  pending,
  hidden,
  rejected,
  rented,
  accepted,
}

extension OwnerPropertyStatusX on OwnerPropertyStatus {
  bool get isVerified => this == OwnerPropertyStatus.verified;
  bool get isPending => this == OwnerPropertyStatus.pending;
  bool get isHidden => this == OwnerPropertyStatus.hidden;
  bool get isRejected => this == OwnerPropertyStatus.rejected;
  bool get isRented => this == OwnerPropertyStatus.rented;
  bool get isAccepted => this == OwnerPropertyStatus.accepted;
  bool get isPublished => isVerified || isAccepted;

  static OwnerPropertyStatus fromName(String? name) {
    if (name == 'under_review') {
      return OwnerPropertyStatus.pending;
    }
    return OwnerPropertyStatus.values.firstWhere(
      (status) => status.name == name,
      orElse: () => OwnerPropertyStatus.pending,
    );
  }
}
