import 'package:equatable/equatable.dart';
import 'package:sokoun_app/features/shared/premium/data/premium_json.dart';

class PromotionBody extends Equatable {
  const PromotionBody({
    this.propertyId = '',
    this.optionId = '',
    this.requestKey = '',
  });
  const PromotionBody.initial() : this();
  factory PromotionBody.fromJson(Map<String, dynamic> json) => PromotionBody(
    propertyId: premiumString(json['property_id']),
    optionId: premiumString(json['option_id']),
    requestKey: premiumString(json['request_key']),
  );
  final String propertyId;
  final String optionId;
  final String requestKey;

  Map<String, dynamic> toJson() => {
    'property_id': propertyId,
    'option_id': optionId,
    'request_key': requestKey,
  };
  PromotionBody copyWith({
    String? propertyId,
    String? optionId,
    String? requestKey,
  }) => PromotionBody(
    propertyId: propertyId ?? this.propertyId,
    optionId: optionId ?? this.optionId,
    requestKey: requestKey ?? this.requestKey,
  );
  @override
  List<Object?> get props => [propertyId, optionId, requestKey];
}
