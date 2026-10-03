import '../enums/owner_revenue_status.dart';
import '../owner_property_json.dart';
import 'package:equatable/equatable.dart';
import 'package:sokoun_app/features/shared/finance/data/egyptian_pound.dart';

class OwnerRevenueContent extends Equatable {
  const OwnerRevenueContent({
    required this.totalThisMonth,
    this.formattedTotal = '',
    this.currency = '',
    this.percentageChange = 0,
    this.comparisonText = '',
    this.isPositive = true,
    this.properties = const [],
    this.transactions = const [],
  });
  const OwnerRevenueContent.initial()
    : totalThisMonth = 0,
      formattedTotal = '',
      currency = '',
      percentageChange = 0,
      comparisonText = '',
      isPositive = true,
      properties = const [],
      transactions = const [];
  factory OwnerRevenueContent.fromJson(
    Map<String, dynamic> json,
  ) => OwnerRevenueContent(
    totalThisMonth:
        EgyptianPound.parseAmount(json['total_this_month'])?.toDouble() ?? 0,
    formattedTotal: json['formatted_total']?.toString() ?? '',
    currency: json['currency']?.toString() ?? '',
    percentageChange: ownerPropertyNumber(json['percentage_change']).toDouble(),
    comparisonText: json['comparison_text']?.toString() ?? '',
    isPositive:
        json['is_positive'] as bool? ??
        ownerPropertyNumber(json['percentage_change']) >= 0,
    properties: ownerPropertyMaps(
      json['properties'],
    ).map(OwnerRevenuePropertyContent.fromJson).toList(growable: false),
    transactions: ownerPropertyMaps(
      json['recent_transactions'],
    ).map(OwnerTransactionContent.fromJson).toList(growable: false),
  );
  final double totalThisMonth, percentageChange;
  final String formattedTotal, currency, comparisonText;
  final bool isPositive;
  final List<OwnerRevenuePropertyContent> properties;
  final List<OwnerTransactionContent> transactions;
  String get totalLabel => EgyptianPound.formatAmount(totalThisMonth);
  Map<String, dynamic> toJson() => {
    'total_this_month': totalThisMonth,
    'formatted_total': formattedTotal,
    'currency': currency,
    'percentage_change': percentageChange,
    'comparison_text': comparisonText,
    'is_positive': isPositive,
    'properties': properties
        .map((item) => item.toJson())
        .toList(growable: false),
    'recent_transactions': transactions
        .map((item) => item.toJson())
        .toList(growable: false),
  };
  OwnerRevenueContent copyWith({
    double? totalThisMonth,
    String? formattedTotal,
    String? currency,
    double? percentageChange,
    String? comparisonText,
    bool? isPositive,
    List<OwnerRevenuePropertyContent>? properties,
    List<OwnerTransactionContent>? transactions,
  }) => OwnerRevenueContent(
    totalThisMonth: totalThisMonth ?? this.totalThisMonth,
    formattedTotal: formattedTotal ?? this.formattedTotal,
    currency: currency ?? this.currency,
    percentageChange: percentageChange ?? this.percentageChange,
    comparisonText: comparisonText ?? this.comparisonText,
    isPositive: isPositive ?? this.isPositive,
    properties: properties ?? this.properties,
    transactions: transactions ?? this.transactions,
  );
  @override
  List<Object?> get props => [
    totalThisMonth,
    formattedTotal,
    currency,
    percentageChange,
    comparisonText,
    isPositive,
    properties,
    transactions,
  ];
}

class OwnerRevenuePropertyContent extends Equatable {
  const OwnerRevenuePropertyContent({
    required this.id,
    required this.title,
    required this.amount,
    required this.dueDate,
    required this.status,
    this.formattedAmount = '',
    this.currency = '',
    this.statusLabel = '',
  });
  const OwnerRevenuePropertyContent.initial()
    : id = '',
      title = '',
      amount = 0,
      dueDate = '',
      status = OwnerRevenueStatus.due,
      formattedAmount = '',
      currency = '',
      statusLabel = '';
  factory OwnerRevenuePropertyContent.fromJson(Map<String, dynamic> json) =>
      OwnerRevenuePropertyContent(
        id: json['id']?.toString() ?? '',
        title: json['title']?.toString() ?? '',
        amount: EgyptianPound.parseAmount(json['amount'])?.toDouble() ?? 0,
        dueDate: json['due_date']?.toString() ?? '',
        status: OwnerRevenueStatusX.fromName(json['status']?.toString()),
        formattedAmount: json['formatted_amount']?.toString() ?? '',
        currency: json['currency']?.toString() ?? '',
        statusLabel: json['status_label']?.toString() ?? '',
      );
  final String id, title, dueDate, formattedAmount, currency, statusLabel;
  final double amount;
  final OwnerRevenueStatus status;
  String get amountLabel => EgyptianPound.formatAmount(amount);
  Map<String, dynamic> toJson() => {
    'id': id,
    'title': title,
    'amount': amount,
    'due_date': dueDate,
    'status': status.name,
    'formatted_amount': formattedAmount,
    'currency': currency,
    'status_label': statusLabel,
  };
  OwnerRevenuePropertyContent copyWith({
    String? id,
    String? title,
    double? amount,
    String? dueDate,
    OwnerRevenueStatus? status,
    String? formattedAmount,
    String? currency,
    String? statusLabel,
  }) => OwnerRevenuePropertyContent(
    id: id ?? this.id,
    title: title ?? this.title,
    amount: amount ?? this.amount,
    dueDate: dueDate ?? this.dueDate,
    status: status ?? this.status,
    formattedAmount: formattedAmount ?? this.formattedAmount,
    currency: currency ?? this.currency,
    statusLabel: statusLabel ?? this.statusLabel,
  );
  @override
  List<Object?> get props => [
    id,
    title,
    amount,
    dueDate,
    status,
    formattedAmount,
    currency,
    statusLabel,
  ];
}

class OwnerTransactionContent extends Equatable {
  const OwnerTransactionContent({
    required this.id,
    required this.title,
    required this.date,
    required this.amount,
    this.formattedAmount = '',
    this.currency = '',
    this.dateIso = '',
    this.type = '',
    bool? isCredit,
  }) : _isCredit = isCredit;
  const OwnerTransactionContent.initial()
    : id = '',
      title = '',
      date = '',
      amount = 0,
      formattedAmount = '',
      currency = '',
      dateIso = '',
      type = '',
      _isCredit = null;
  factory OwnerTransactionContent.fromJson(Map<String, dynamic> json) =>
      OwnerTransactionContent(
        id: json['id']?.toString() ?? '',
        title: json['title']?.toString() ?? '',
        date: json['date']?.toString() ?? '',
        amount: EgyptianPound.parseAmount(json['amount'])?.toDouble() ?? 0,
        formattedAmount: json['formatted_amount']?.toString() ?? '',
        currency: json['currency']?.toString() ?? '',
        dateIso: json['date_iso']?.toString() ?? '',
        type: json['type']?.toString() ?? '',
        isCredit: json['is_credit'] as bool?,
      );
  final String id, title, date, formattedAmount, currency, dateIso, type;
  final double amount;
  final bool? _isCredit;
  bool get isCredit => _isCredit ?? amount >= 0;
  String get amountLabel => EgyptianPound.formatAmount(amount.abs());
  Map<String, dynamic> toJson() => {
    'id': id,
    'title': title,
    'date': date,
    'amount': amount,
    'formatted_amount': formattedAmount,
    'currency': currency,
    'date_iso': dateIso,
    'type': type,
    if (_isCredit != null) 'is_credit': _isCredit,
  };
  OwnerTransactionContent copyWith({
    String? id,
    String? title,
    String? date,
    double? amount,
    String? formattedAmount,
    String? currency,
    String? dateIso,
    String? type,
    bool? isCredit,
  }) => OwnerTransactionContent(
    id: id ?? this.id,
    title: title ?? this.title,
    date: date ?? this.date,
    amount: amount ?? this.amount,
    formattedAmount: formattedAmount ?? this.formattedAmount,
    currency: currency ?? this.currency,
    dateIso: dateIso ?? this.dateIso,
    type: type ?? this.type,
    isCredit: isCredit ?? _isCredit,
  );
  @override
  List<Object?> get props => [
    id,
    title,
    date,
    amount,
    formattedAmount,
    currency,
    dateIso,
    type,
    _isCredit,
  ];
}
