enum OwnerRevenueStatus { paid, due, late, upcoming }

extension OwnerRevenueStatusX on OwnerRevenueStatus {
  bool get isPaid => this == OwnerRevenueStatus.paid;
  bool get isDue =>
      this == OwnerRevenueStatus.due || this == OwnerRevenueStatus.upcoming;
  bool get isLate => this == OwnerRevenueStatus.late;

  static OwnerRevenueStatus fromName(String? name) {
    return OwnerRevenueStatus.values.firstWhere(
      (status) => status.name == name,
      orElse: () => OwnerRevenueStatus.due,
    );
  }
}
