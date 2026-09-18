part of '../../imports.dart';

class OwnerRevenuePropertyContent extends Equatable {
  const OwnerRevenuePropertyContent({
    required this.id,
    required this.title,
    required this.amount,
    required this.dueDate,
    required this.status,
  });

  factory OwnerRevenuePropertyContent.initial() {
    return const OwnerRevenuePropertyContent(
      id: '',
      title: '',
      amount: 0,
      dueDate: '',
      status: OwnerRevenueStatus.due,
    );
  }

  factory OwnerRevenuePropertyContent.fromJson(Map<String, dynamic> json) {
    return OwnerRevenuePropertyContent(
      id: json['id'] ?? '',
      title: json['title'] ?? '',
      amount: json['amount'] ?? 0,
      dueDate: json['due_date'] ?? '',
      status: OwnerRevenueStatusX.fromName(json['status']),
    );
  }

  final String id;
  final String title;
  final int amount;
  final String dueDate;
  final OwnerRevenueStatus status;

  Map<String, dynamic> toJson() {
    return {
      'id': id,
      'title': title,
      'amount': amount,
      'due_date': dueDate,
      'status': status.name,
    };
  }

  OwnerRevenuePropertyContent copyWith({
    String? id,
    String? title,
    int? amount,
    String? dueDate,
    OwnerRevenueStatus? status,
  }) {
    return OwnerRevenuePropertyContent(
      id: id ?? this.id,
      title: title ?? this.title,
      amount: amount ?? this.amount,
      dueDate: dueDate ?? this.dueDate,
      status: status ?? this.status,
    );
  }

  @override
  List<Object?> get props => [id, title, amount, dueDate, status];
}

class OwnerTransactionContent extends Equatable {
  const OwnerTransactionContent({
    required this.id,
    required this.title,
    required this.date,
    required this.amount,
  });

  factory OwnerTransactionContent.initial() {
    return const OwnerTransactionContent(
      id: '',
      title: '',
      date: '',
      amount: 0,
    );
  }

  factory OwnerTransactionContent.fromJson(Map<String, dynamic> json) {
    return OwnerTransactionContent(
      id: json['id'] ?? '',
      title: json['title'] ?? '',
      date: json['date'] ?? '',
      amount: json['amount'] ?? 0,
    );
  }

  final String id;
  final String title;
  final String date;
  final int amount;

  bool get isCredit => amount >= 0;

  Map<String, dynamic> toJson() {
    return {'id': id, 'title': title, 'date': date, 'amount': amount};
  }

  OwnerTransactionContent copyWith({
    String? id,
    String? title,
    String? date,
    int? amount,
  }) {
    return OwnerTransactionContent(
      id: id ?? this.id,
      title: title ?? this.title,
      date: date ?? this.date,
      amount: amount ?? this.amount,
    );
  }

  @override
  List<Object?> get props => [id, title, date, amount];
}
