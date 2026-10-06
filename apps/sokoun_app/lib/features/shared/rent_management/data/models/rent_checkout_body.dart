import 'package:equatable/equatable.dart';
import 'package:sokoun_app/features/shared/premium/data/premium_json.dart';

class RentCheckoutBody extends Equatable {
  const RentCheckoutBody({this.invoiceId = '', this.requestKey = ''});
  const RentCheckoutBody.initial() : this();
  factory RentCheckoutBody.fromJson(Map<String, dynamic> json) =>
      RentCheckoutBody(
        invoiceId: premiumString(json['invoice_id']),
        requestKey: premiumString(json['request_key']),
      );
  final String invoiceId;
  final String requestKey;

  Map<String, dynamic> toJson() => {
    'invoice_id': invoiceId,
    'request_key': requestKey,
  };
  RentCheckoutBody copyWith({String? invoiceId, String? requestKey}) =>
      RentCheckoutBody(
        invoiceId: invoiceId ?? this.invoiceId,
        requestKey: requestKey ?? this.requestKey,
      );
  @override
  List<Object?> get props => [invoiceId, requestKey];
}
