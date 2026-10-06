import 'package:equatable/equatable.dart';

class OwnerPropertyDeletionModel extends Equatable {
  const OwnerPropertyDeletionModel({required this.id, required this.deleted});
  const OwnerPropertyDeletionModel.initial() : id = '', deleted = false;

  factory OwnerPropertyDeletionModel.fromJson(Map<String, dynamic> json) =>
      OwnerPropertyDeletionModel(
        id: json['id']?.toString() ?? '',
        deleted: json['deleted'] == true,
      );

  final String id;
  final bool deleted;

  bool confirms(String propertyId) => deleted && id == propertyId;
  Map<String, dynamic> toJson() => {'id': id, 'deleted': deleted};

  OwnerPropertyDeletionModel copyWith({String? id, bool? deleted}) =>
      OwnerPropertyDeletionModel(
        id: id ?? this.id,
        deleted: deleted ?? this.deleted,
      );

  @override
  List<Object?> get props => [id, deleted];
}
