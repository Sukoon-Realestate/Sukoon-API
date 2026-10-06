import 'package:equatable/equatable.dart';
import 'package:sokoun_app/features/shared/premium/data/premium_json.dart';

class LeaseTemplate extends Equatable {
  const LeaseTemplate({
    this.id = '',
    this.title = '',
    this.jurisdiction = '',
    this.language = '',
    this.version = '',
  });
  const LeaseTemplate.initial() : this();
  factory LeaseTemplate.fromJson(Map<String, dynamic> json) => LeaseTemplate(
    id: premiumString(json['id']),
    title: premiumString(json['title']),
    jurisdiction: premiumString(json['jurisdiction']),
    language: premiumString(json['language']),
    version: premiumString(json['version']),
  );
  final String id;
  final String title;
  final String jurisdiction;
  final String language;
  final String version;

  Map<String, dynamic> toJson() => {
    'id': id,
    'title': title,
    'jurisdiction': jurisdiction,
    'language': language,
    'version': version,
  };
  LeaseTemplate copyWith({
    String? id,
    String? title,
    String? jurisdiction,
    String? language,
    String? version,
  }) => LeaseTemplate(
    id: id ?? this.id,
    title: title ?? this.title,
    jurisdiction: jurisdiction ?? this.jurisdiction,
    language: language ?? this.language,
    version: version ?? this.version,
  );
  @override
  List<Object?> get props => [id, title, jurisdiction, language, version];
}
