part of '../../imports.dart';

enum OwnerPropertyAction { edit, pause, markRented, delete }

extension OwnerPropertyActionX on OwnerPropertyAction {
  bool get isEdit => this == OwnerPropertyAction.edit;
  bool get isPause => this == OwnerPropertyAction.pause;
  bool get isMarkRented => this == OwnerPropertyAction.markRented;
  bool get isDelete => this == OwnerPropertyAction.delete;

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
