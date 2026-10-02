part of '../../imports.dart';

class ProfileCity extends Equatable {
  const ProfileCity({required this.id, required this.name, required this.slug});
  const ProfileCity.initial() : id = '', name = '', slug = '';

  factory ProfileCity.fromJson(Map<String, dynamic> json) => ProfileCity(
    id: _profileString(json['id']),
    name: _profileString(json['name']),
    slug: _profileString(json['slug']),
  );

  final String id, name, slug;
  Map<String, dynamic> toJson() => {'id': id, 'name': name, 'slug': slug};
  ProfileCity copyWith({String? id, String? name, String? slug}) => ProfileCity(
    id: id ?? this.id,
    name: name ?? this.name,
    slug: slug ?? this.slug,
  );
  @override
  List<Object?> get props => [id, name, slug];
}
