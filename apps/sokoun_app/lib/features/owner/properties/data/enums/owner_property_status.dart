part of '../../imports.dart';

enum OwnerPropertyStatus { verified, pending, hidden, rejected, rented }

extension OwnerPropertyStatusX on OwnerPropertyStatus {
  bool get isVerified => this == OwnerPropertyStatus.verified;
  bool get isPending => this == OwnerPropertyStatus.pending;
  bool get isHidden => this == OwnerPropertyStatus.hidden;
  bool get isRejected => this == OwnerPropertyStatus.rejected;
  bool get isRented => this == OwnerPropertyStatus.rented;

  String get label {
    if (isVerified) {
      return LocaleKeys.ownerPropertyStatusVerified;
    }
    if (isPending) {
      return LocaleKeys.ownerPropertyStatusPending;
    }
    if (isHidden) {
      return LocaleKeys.ownerPropertyStatusHidden;
    }
    if (isRejected) {
      return LocaleKeys.ownerPropertyStatusRejected;
    }
    return LocaleKeys.ownerPropertyStatusRented;
  }

  IconData get icon {
    if (isVerified) {
      return Icons.verified_rounded;
    }
    if (isPending) {
      return Icons.schedule_rounded;
    }
    if (isHidden) {
      return Icons.visibility_off_outlined;
    }
    if (isRejected) {
      return Icons.error_outline_rounded;
    }
    return Icons.task_alt_rounded;
  }

  Color get foregroundColor {
    if (isVerified) {
      return AppColors.gold;
    }
    if (isPending) {
      return AppColors.amber;
    }
    if (isHidden) {
      return AppColors.sokoonGray;
    }
    if (isRejected) {
      return AppColors.red;
    }
    return AppColors.green;
  }

  Color get backgroundColor {
    if (isVerified) {
      return AppColors.goldPale;
    }
    if (isPending) {
      return AppColors.orangePale;
    }
    if (isHidden) {
      return AppColors.grayBackground;
    }
    if (isRejected) {
      return AppColors.redPale;
    }
    return AppColors.greenPale;
  }

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
