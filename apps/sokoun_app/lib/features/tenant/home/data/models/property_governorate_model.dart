import 'package:equatable/equatable.dart';

class PropertyGovernorateModel extends Equatable {
  const PropertyGovernorateModel({
    required this.id,
    required this.name,
    required this.slug,
    required this.createdAt,
    required this.updatedAt,
  });

  const PropertyGovernorateModel.initial()
    : id = '',
      name = '',
      slug = '',
      createdAt = '',
      updatedAt = '';

  factory PropertyGovernorateModel.fromJson(Map<String, dynamic> json) =>
      PropertyGovernorateModel(
        id: json['id']?.toString() ?? '',
        name: json['name']?.toString() ?? '',
        slug: json['slug']?.toString() ?? '',
        createdAt: json['created_at']?.toString() ?? '',
        updatedAt: json['updated_at']?.toString() ?? '',
      );

  final String id;
  final String name;
  final String slug;
  final String createdAt;
  final String updatedAt;

  Map<String, dynamic> toJson() => {
    'id': id,
    'name': name,
    'slug': slug,
    'created_at': createdAt,
    'updated_at': updatedAt,
  };

  PropertyGovernorateModel copyWith({
    String? id,
    String? name,
    String? slug,
    String? createdAt,
    String? updatedAt,
  }) => PropertyGovernorateModel(
    id: id ?? this.id,
    name: name ?? this.name,
    slug: slug ?? this.slug,
    createdAt: createdAt ?? this.createdAt,
    updatedAt: updatedAt ?? this.updatedAt,
  );

  @override
  List<Object?> get props => [id, name, slug, createdAt, updatedAt];
}
