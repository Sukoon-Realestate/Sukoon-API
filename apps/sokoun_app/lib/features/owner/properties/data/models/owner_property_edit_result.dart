part of '../../imports.dart';

class OwnerPropertyEditResult {
  const OwnerPropertyEditResult({
    required this.property,
    required this.isDeleted,
  });

  factory OwnerPropertyEditResult.initial() {
    return OwnerPropertyEditResult(
      property: OwnerPropertyContent.initial(),
      isDeleted: false,
    );
  }

  factory OwnerPropertyEditResult.saved(OwnerPropertyContent property) {
    return OwnerPropertyEditResult(property: property, isDeleted: false);
  }

  factory OwnerPropertyEditResult.deleted(OwnerPropertyContent property) {
    return OwnerPropertyEditResult(property: property, isDeleted: true);
  }

  factory OwnerPropertyEditResult.fromJson(Map<String, dynamic> json) {
    return OwnerPropertyEditResult(
      property: OwnerPropertyContent.fromJson(json['property'] ?? {}),
      isDeleted: json['is_deleted'] ?? false,
    );
  }

  final OwnerPropertyContent property;
  final bool isDeleted;

  Map<String, dynamic> toJson() {
    return {'property': property.toJson(), 'is_deleted': isDeleted};
  }

  OwnerPropertyEditResult copyWith({
    OwnerPropertyContent? property,
    bool? isDeleted,
  }) {
    return OwnerPropertyEditResult(
      property: property ?? this.property,
      isDeleted: isDeleted ?? this.isDeleted,
    );
  }
}
