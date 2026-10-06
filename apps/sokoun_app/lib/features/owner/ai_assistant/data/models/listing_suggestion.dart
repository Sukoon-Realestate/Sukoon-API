import 'package:equatable/equatable.dart';
import 'package:sokoun_app/features/shared/premium/data/premium_json.dart';

class ListingSuggestion extends Equatable {
  const ListingSuggestion({
    this.id = '',
    this.propertyId = '',
    this.suggestedTitle = '',
    this.suggestedDescription = '',
    this.warnings = const [],
  });
  const ListingSuggestion.initial() : this();
  factory ListingSuggestion.fromJson(Map<String, dynamic> json) =>
      ListingSuggestion(
        id: premiumString(json['id']),
        propertyId: premiumString(json['property_id']),
        suggestedTitle: premiumString(json['suggested_title']),
        suggestedDescription: premiumString(json['suggested_description']),
        warnings:
            (json['warnings'] is List ? json['warnings'] as List : const [])
                .whereType<String>()
                .toList(growable: false),
      );
  final String id;
  final String propertyId;
  final String suggestedTitle;
  final String suggestedDescription;
  final List<String> warnings;

  Map<String, dynamic> toJson() => {
    'id': id,
    'property_id': propertyId,
    'suggested_title': suggestedTitle,
    'suggested_description': suggestedDescription,
    'warnings': warnings,
  };
  ListingSuggestion copyWith({
    String? id,
    String? propertyId,
    String? suggestedTitle,
    String? suggestedDescription,
    List<String>? warnings,
  }) => ListingSuggestion(
    id: id ?? this.id,
    propertyId: propertyId ?? this.propertyId,
    suggestedTitle: suggestedTitle ?? this.suggestedTitle,
    suggestedDescription: suggestedDescription ?? this.suggestedDescription,
    warnings: warnings ?? this.warnings,
  );
  @override
  List<Object?> get props => [
    id,
    propertyId,
    suggestedTitle,
    suggestedDescription,
    warnings,
  ];
}
