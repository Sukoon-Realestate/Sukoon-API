part of '../../imports.dart';

extension OwnerPropertyStatusPresentation on OwnerPropertyStatus {
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
}

extension OwnerRevenueStatusPresentation on OwnerRevenueStatus {
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
}

extension OwnerPropertyActionPresentation on OwnerPropertyAction {
  String label({required bool isHidden}) {
    if (isEdit) {
      return LocaleKeys.ownerPropertiesEditProperty;
    }
    if (isPause) {
      return isHidden
          ? LocaleKeys.ownerPropertiesReactivate
          : LocaleKeys.ownerPropertiesPause;
    }
    if (isMarkRented) {
      return LocaleKeys.ownerPropertiesMarkRented;
    }
    return LocaleKeys.ownerPropertiesDeleteProperty;
  }

  IconData get icon {
    if (isEdit) {
      return Icons.edit_outlined;
    }
    if (isPause) {
      return Icons.pause_circle_outline_rounded;
    }
    if (isMarkRented) {
      return Icons.task_alt_rounded;
    }
    return Icons.delete_outline_rounded;
  }

  Color get foregroundColor {
    if (isEdit) {
      return AppColors.sokoonTeal;
    }
    if (isPause) {
      return AppColors.amber;
    }
    if (isMarkRented) {
      return AppColors.green;
    }
    return AppColors.red;
  }

  Color get backgroundColor {
    if (isEdit) {
      return AppColors.mintLight;
    }
    if (isPause) {
      return AppColors.orangePale;
    }
    if (isMarkRented) {
      return AppColors.greenPale;
    }
    return AppColors.redPale;
  }
}
