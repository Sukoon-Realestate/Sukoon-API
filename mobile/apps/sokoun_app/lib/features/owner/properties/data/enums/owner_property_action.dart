enum OwnerPropertyAction { edit, pause, markRented, delete }

extension OwnerPropertyActionX on OwnerPropertyAction {
  bool get isEdit => this == OwnerPropertyAction.edit;
  bool get isPause => this == OwnerPropertyAction.pause;
  bool get isMarkRented => this == OwnerPropertyAction.markRented;
  bool get isDelete => this == OwnerPropertyAction.delete;
}
