import 'package:equatable/equatable.dart';

class OwnerPropertyLocationsResponse extends Equatable {
  const OwnerPropertyLocationsResponse({
    required this.count,
    required this.results,
    this.next,
    this.previous,
  });

  const OwnerPropertyLocationsResponse.initial()
    : count = 0,
      results = const [],
      next = null,
      previous = null;

  factory OwnerPropertyLocationsResponse.fromJson(Map<String, dynamic> json) {
    final List<OwnerPropertyLocationModel> results =
        (json['results'] as List?)
            ?.whereType<Map>()
            .map(
              (item) => OwnerPropertyLocationModel.fromJson(
                Map<String, dynamic>.from(item),
              ),
            )
            .toList(growable: false) ??
        const [];

    return OwnerPropertyLocationsResponse(
      count: (json['count'] as num?)?.toInt() ?? results.length,
      next: json['next'] as String?,
      previous: json['previous'] as String?,
      results: results,
    );
  }

  final int count;
  final String? next;
  final String? previous;
  final List<OwnerPropertyLocationModel> results;

  Map<String, dynamic> toJson() => {
    'count': count,
    'next': next,
    'previous': previous,
    'results': results.map((item) => item.toJson()).toList(growable: false),
  };

  OwnerPropertyLocationsResponse copyWith({
    int? count,
    String? next,
    String? previous,
    List<OwnerPropertyLocationModel>? results,
  }) {
    return OwnerPropertyLocationsResponse(
      count: count ?? this.count,
      next: next ?? this.next,
      previous: previous ?? this.previous,
      results: results ?? this.results,
    );
  }

  @override
  List<Object?> get props => [count, next, previous, results];
}

class OwnerPropertyLocationModel extends Equatable {
  const OwnerPropertyLocationModel({
    required this.id,
    required this.name,
    required this.slug,
    required this.createdAt,
    required this.updatedAt,
  });

  const OwnerPropertyLocationModel.initial()
    : id = '',
      name = '',
      slug = '',
      createdAt = '',
      updatedAt = '';

  factory OwnerPropertyLocationModel.fromJson(Map<String, dynamic> json) {
    return OwnerPropertyLocationModel(
      id: json['id'] as String? ?? '',
      name: json['name'] as String? ?? '',
      slug: json['slug'] as String? ?? '',
      createdAt: json['created_at'] as String? ?? '',
      updatedAt: json['updated_at'] as String? ?? '',
    );
  }

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

  OwnerPropertyLocationModel copyWith({
    String? id,
    String? name,
    String? slug,
    String? createdAt,
    String? updatedAt,
  }) {
    return OwnerPropertyLocationModel(
      id: id ?? this.id,
      name: name ?? this.name,
      slug: slug ?? this.slug,
      createdAt: createdAt ?? this.createdAt,
      updatedAt: updatedAt ?? this.updatedAt,
    );
  }

  @override
  List<Object?> get props => [id, name, slug, createdAt, updatedAt];
}
