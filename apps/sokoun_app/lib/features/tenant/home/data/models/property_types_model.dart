import 'package:equatable/equatable.dart';

class PropertyTypesModel extends Equatable {
  const PropertyTypesModel({
    required this.count,
    required this.results,
    this.next,
    this.previous,
  });

  const PropertyTypesModel.initial()
    : count = 5,
      next = null,
      previous = null,
      results = const [
        PropertyTypeModel.initial(),
        PropertyTypeModel.initial(),
        PropertyTypeModel.initial(),
        PropertyTypeModel.initial(),
        PropertyTypeModel.initial(),
      ];

  factory PropertyTypesModel.fromJson(Map<String, dynamic> json) {
    return PropertyTypesModel(
      count: (json['count'] as num?)?.toInt() ?? 0,
      next: json['next'],
      previous: json['previous'],
      results:
          (json['results'] as List?)
              ?.map(
                (item) =>
                    PropertyTypeModel.fromJson(item as Map<String, dynamic>),
              )
              .toList() ??
          [],
    );
  }

  final int count;
  final String? next;
  final String? previous;
  final List<PropertyTypeModel> results;

  Map<String, dynamic> toJson() => {
    'count': count,
    'next': next,
    'previous': previous,
    'results': results.map((item) => item.toJson()).toList(),
  };

  PropertyTypesModel copyWith({
    int? count,
    String? next,
    String? previous,
    List<PropertyTypeModel>? results,
  }) {
    return PropertyTypesModel(
      count: count ?? this.count,
      next: next ?? this.next,
      previous: previous ?? this.previous,
      results: results ?? this.results,
    );
  }

  @override
  List<Object?> get props => [count, next, previous, results];
}

class PropertyTypeModel extends Equatable {
  const PropertyTypeModel({
    required this.id,
    required this.name,
    required this.slug,
    required this.description,
  });

  const PropertyTypeModel.initial()
    : id = '',
      name = '',
      slug = '',
      description = '';

  factory PropertyTypeModel.fromJson(Map<String, dynamic> json) {
    return PropertyTypeModel(
      id: json['id'] ?? '',
      name: json['name'] ?? '',
      slug: json['slug'] ?? '',
      description: json['description'] ?? '',
    );
  }

  final String id;
  final String name;
  final String slug;
  final String description;

  Map<String, dynamic> toJson() => {
    'id': id,
    'name': name,
    'slug': slug,
    'description': description,
  };

  PropertyTypeModel copyWith({
    String? id,
    String? name,
    String? slug,
    String? description,
  }) {
    return PropertyTypeModel(
      id: id ?? this.id,
      name: name ?? this.name,
      slug: slug ?? this.slug,
      description: description ?? this.description,
    );
  }

  @override
  List<Object?> get props => [id, name, slug, description];
}
