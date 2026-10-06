import 'package:equatable/equatable.dart';

class PublicPageContent extends Equatable {
  const PublicPageContent({
    required this.slug,
    required this.title,
    required this.content,
    required this.contentFormat,
    required this.language,
    required this.updatedAt,
  });
  const PublicPageContent.initial()
    : slug = '',
      title = '',
      content = '',
      contentFormat = 'plain_text',
      language = '',
      updatedAt = '';

  factory PublicPageContent.fromJson(Map<String, dynamic> json) =>
      PublicPageContent(
        slug: json['slug']?.toString() ?? '',
        title: json['title']?.toString() ?? '',
        content: json['content']?.toString() ?? '',
        contentFormat: json['content_format']?.toString() ?? 'plain_text',
        language: json['language']?.toString() ?? '',
        updatedAt: json['updated_at']?.toString() ?? '',
      );
  final String slug;
  final String title;
  final String content;
  final String contentFormat;
  final String language;
  final String updatedAt;

  Map<String, dynamic> toJson() => {
    'slug': slug,
    'title': title,
    'content': content,
    'content_format': contentFormat,
    'language': language,
    'updated_at': updatedAt,
  };
  PublicPageContent copyWith({
    String? slug,
    String? title,
    String? content,
    String? contentFormat,
    String? language,
    String? updatedAt,
  }) => PublicPageContent(
    slug: slug ?? this.slug,
    title: title ?? this.title,
    content: content ?? this.content,
    contentFormat: contentFormat ?? this.contentFormat,
    language: language ?? this.language,
    updatedAt: updatedAt ?? this.updatedAt,
  );
  @override
  List<Object?> get props => [
    slug,
    title,
    content,
    contentFormat,
    language,
    updatedAt,
  ];
}
