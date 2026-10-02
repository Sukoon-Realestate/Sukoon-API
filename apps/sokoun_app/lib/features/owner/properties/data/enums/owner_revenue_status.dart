part of '../../imports.dart';

enum OwnerRevenueStatus { paid, due, late, upcoming }

extension OwnerRevenueStatusX on OwnerRevenueStatus {
  bool get isPaid => this == OwnerRevenueStatus.paid;
  bool get isDue =>
      this == OwnerRevenueStatus.due || this == OwnerRevenueStatus.upcoming;
  bool get isLate => this == OwnerRevenueStatus.late;

  String get label {
    if (isPaid) {
      return LocaleKeys.ownerRevenuePaid;
    }
    if (isDue) {
      return this == OwnerRevenueStatus.upcoming
          ? LocaleKeys.ownerRevenueUpcoming
          : LocaleKeys.ownerRevenueDue;
    }
    return LocaleKeys.ownerRevenueLate;
  }

  Color get foregroundColor {
    if (isPaid) {
      return AppColors.green;
    }
    if (isDue) {
      return AppColors.amber;
    }
    return AppColors.red;
  }

  Color get backgroundColor {
    if (isPaid) {
      return AppColors.greenPale;
    }
    if (isDue) {
      return AppColors.orangePale;
    }
    return AppColors.redPale;
  }

  static OwnerRevenueStatus fromName(String? name) {
    return OwnerRevenueStatus.values.firstWhere(
      (status) => status.name == name,
      orElse: () => OwnerRevenueStatus.due,
    );
  }
}
