
import '../../../config/res/config_imports.dart';

class DropDownModel {
  final int id;
  final String name;

  DropDownModel({
    required this.id,
    required this.name,
  });

  factory DropDownModel.initial() {
    return DropDownModel(
      id: ConstantManager.zero,
      name: ConstantManager.emptyText,
    );
  }

  factory DropDownModel.fromJson(Map<String, dynamic> json) {
    return DropDownModel(
      id: json['id'],
      name: json['name'],
    );
  }

  Map<String, dynamic> toJson() => {'id': id, 'name': name};

  @override
  bool operator ==(Object other) =>
      identical(this, other) ||
      other is DropDownModel &&
          runtimeType == other.runtimeType &&
          id == other.id;

  @override
  int get hashCode => id.hashCode;

  @override
  String toString() => 'DropDownModel(id: $id, name: $name)';
}
