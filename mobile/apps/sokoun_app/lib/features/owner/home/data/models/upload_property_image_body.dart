import 'dart:io';

class UploadPropertyImageBody {
  const UploadPropertyImageBody({
    required this.image,
    this.name = '',
    this.description = '',
  });

  const UploadPropertyImageBody.initial()
    : image = null,
      name = '',
      description = '';

  factory UploadPropertyImageBody.fromJson(Map<String, dynamic> json) =>
      UploadPropertyImageBody(
        image: json['image'] is File ? json['image'] as File : null,
        name: json['name'] as String? ?? '',
        description: json['description'] as String? ?? '',
      );

  final File? image;
  final String name;
  final String description;

  Map<String, dynamic> toJson() => {
    'image': image,
    'name': name.trim(),
    'description': description.trim(),
  };

  UploadPropertyImageBody copyWith({
    File? image,
    String? name,
    String? description,
  }) => UploadPropertyImageBody(
    image: image ?? this.image,
    name: name ?? this.name,
    description: description ?? this.description,
  );
}
