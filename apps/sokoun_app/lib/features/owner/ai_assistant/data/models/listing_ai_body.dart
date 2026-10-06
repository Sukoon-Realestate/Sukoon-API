import 'package:equatable/equatable.dart';
import 'package:sokoun_app/features/shared/premium/data/premium_json.dart';
import 'listing_ai_facts.dart';

class ListingAiBody extends Equatable {
  const ListingAiBody({
    this.propertyId = '',
    this.facts = const ListingAiFacts.initial(),
    this.language = '',
    this.requestKey = '',
  });
  const ListingAiBody.initial() : this();
  factory ListingAiBody.fromJson(Map<String, dynamic> json) => ListingAiBody(
    propertyId: premiumString(json['property_id']),
    facts: ListingAiFacts.fromJson(premiumMap(json['facts'])),
    language: premiumString(json['language']),
    requestKey: premiumString(json['request_key']),
  );
  final String propertyId;
  final ListingAiFacts facts;
  final String language;
  final String requestKey;

  Map<String, dynamic> toJson() => {
    'property_id': propertyId,
    'facts': facts.toJson(),
    'language': language,
    'request_key': requestKey,
  };
  ListingAiBody copyWith({
    String? propertyId,
    ListingAiFacts? facts,
    String? language,
    String? requestKey,
  }) => ListingAiBody(
    propertyId: propertyId ?? this.propertyId,
    facts: facts ?? this.facts,
    language: language ?? this.language,
    requestKey: requestKey ?? this.requestKey,
  );
  @override
  List<Object?> get props => [propertyId, facts, language, requestKey];
}
