import 'package:equatable/equatable.dart';
import 'package:sokoun_app/features/shared/premium/data/premium_json.dart';
import 'package:sokoun_app/features/shared/premium/data/enums/premium_status.dart';
import 'package:sokoun_app/features/shared/premium/data/models/premium_money.dart';

class RentInvoice extends Equatable {
  const RentInvoice({
    this.id = '',
    this.leaseId = '',
    this.propertyTitle = '',
    this.reference = '',
    this.dueDate,
    this.amount = const PremiumMoney.initial(),
    this.status = PremiumStatus.unknown,
    this.receiptUrl = '',
    this.canPay = false,
  });
  const RentInvoice.initial() : this();
  factory RentInvoice.fromJson(Map<String, dynamic> json) => RentInvoice(
    id: premiumString(json['id']),
    leaseId: premiumString(json['lease_id']),
    propertyTitle: premiumString(json['property_title']),
    reference: premiumString(json['reference']),
    dueDate: premiumDate(json['due_date']),
    amount: PremiumMoney.fromJson(premiumMap(json['amount'])),
    status: PremiumStatus.fromValue(json['status']),
    receiptUrl: premiumString(json['receipt_url']),
    canPay: json['can_pay'] == true,
  );
  final String id;
  final String leaseId;
  final String propertyTitle;
  final String reference;
  final DateTime? dueDate;
  final PremiumMoney amount;
  final PremiumStatus status;
  final String receiptUrl;
  final bool canPay;

  Map<String, dynamic> toJson() => {
    'id': id,
    'lease_id': leaseId,
    'property_title': propertyTitle,
    'reference': reference,
    'due_date': dueDate?.toIso8601String(),
    'amount': amount.toJson(),
    'status': status.name,
    'receipt_url': receiptUrl,
    'can_pay': canPay,
  };
  RentInvoice copyWith({
    String? id,
    String? leaseId,
    String? propertyTitle,
    String? reference,
    DateTime? dueDate,
    PremiumMoney? amount,
    PremiumStatus? status,
    String? receiptUrl,
    bool? canPay,
  }) => RentInvoice(
    id: id ?? this.id,
    leaseId: leaseId ?? this.leaseId,
    propertyTitle: propertyTitle ?? this.propertyTitle,
    reference: reference ?? this.reference,
    dueDate: dueDate ?? this.dueDate,
    amount: amount ?? this.amount,
    status: status ?? this.status,
    receiptUrl: receiptUrl ?? this.receiptUrl,
    canPay: canPay ?? this.canPay,
  );
  @override
  List<Object?> get props => [
    id,
    leaseId,
    propertyTitle,
    reference,
    dueDate,
    amount,
    status,
    receiptUrl,
    canPay,
  ];
}
