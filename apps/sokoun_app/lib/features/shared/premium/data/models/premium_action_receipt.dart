import 'package:equatable/equatable.dart';
import '../premium_json.dart';
import 'premium_money.dart';
import 'package:sokoun_app/features/shared/premium/data/enums/premium_status.dart';

class PremiumActionReceipt extends Equatable {
  const PremiumActionReceipt({
    this.id = '',
    this.status = PremiumStatus.unknown,
    this.subjectId = '',
    this.amount = const PremiumMoney.initial(),
    this.message = '',
    this.hostedUrl = '',
    this.expiresAt,
  });
  const PremiumActionReceipt.initial() : this();
  factory PremiumActionReceipt.fromJson(Map<String, dynamic> json) =>
      PremiumActionReceipt(
        id: premiumString(json['id']),
        status: PremiumStatus.fromValue(json['status']),
        subjectId: premiumString(json['subject_id']),
        amount: PremiumMoney.fromJson(premiumMap(json['amount'])),
        message: premiumString(json['message']),
        hostedUrl: premiumString(json['hosted_url']),
        expiresAt: premiumDate(json['expires_at']),
      );
  final String id;
  final PremiumStatus status;
  final String subjectId;
  final PremiumMoney amount;
  final String message;
  final String hostedUrl;
  final DateTime? expiresAt;
  bool get isValid =>
      id.isNotEmpty &&
      status != PremiumStatus.unknown &&
      status != PremiumStatus.failed;
  Map<String, dynamic> toJson() => {
    'id': id,
    'status': status.name,
    'subject_id': subjectId,
    'amount': amount.toJson(),
    'message': message,
    'hosted_url': hostedUrl,
    'expires_at': expiresAt?.toIso8601String(),
  };
  PremiumActionReceipt copyWith({
    String? id,
    PremiumStatus? status,
    String? subjectId,
    PremiumMoney? amount,
    String? message,
    String? hostedUrl,
    DateTime? expiresAt,
  }) => PremiumActionReceipt(
    id: id ?? this.id,
    status: status ?? this.status,
    subjectId: subjectId ?? this.subjectId,
    amount: amount ?? this.amount,
    message: message ?? this.message,
    hostedUrl: hostedUrl ?? this.hostedUrl,
    expiresAt: expiresAt ?? this.expiresAt,
  );
  @override
  List<Object?> get props => [
    id,
    status,
    subjectId,
    amount,
    message,
    hostedUrl,
    expiresAt,
  ];
}
