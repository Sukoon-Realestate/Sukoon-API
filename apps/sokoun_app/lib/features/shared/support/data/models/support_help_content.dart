import 'package:equatable/equatable.dart';
import '../support_json.dart';

class SupportFaq extends Equatable {
  const SupportFaq({
    required this.id,
    required this.question,
    required this.answer,
  });
  const SupportFaq.initial() : id = '', question = '', answer = '';
  factory SupportFaq.fromJson(Map<String, dynamic> json) => SupportFaq(
    id: json['id']?.toString() ?? '',
    question: json['question']?.toString() ?? '',
    answer: json['answer']?.toString() ?? '',
  );
  final String id;
  final String question;
  final String answer;
  Map<String, dynamic> toJson() => {
    'id': id,
    'question': question,
    'answer': answer,
  };
  SupportFaq copyWith({String? id, String? question, String? answer}) =>
      SupportFaq(
        id: id ?? this.id,
        question: question ?? this.question,
        answer: answer ?? this.answer,
      );
  @override
  List<Object?> get props => [id, question, answer];
}

class SupportHelpContent extends Equatable {
  const SupportHelpContent({
    required this.faqs,
    required this.phone,
    required this.email,
    required this.hours,
  });
  const SupportHelpContent.initial()
    : faqs = const [],
      phone = '',
      email = '',
      hours = '';
  factory SupportHelpContent.fromJson(Map<String, dynamic> json) =>
      SupportHelpContent(
        faqs: supportList(json['faqs'], SupportFaq.fromJson),
        phone: json['phone']?.toString() ?? '',
        email: json['email']?.toString() ?? '',
        hours: json['hours']?.toString() ?? '',
      );
  final List<SupportFaq> faqs;
  final String phone;
  final String email;
  final String hours;
  Map<String, dynamic> toJson() => {
    'faqs': faqs.map((item) => item.toJson()).toList(),
    'phone': phone,
    'email': email,
    'hours': hours,
  };
  SupportHelpContent copyWith({
    List<SupportFaq>? faqs,
    String? phone,
    String? email,
    String? hours,
  }) => SupportHelpContent(
    faqs: faqs ?? this.faqs,
    phone: phone ?? this.phone,
    email: email ?? this.email,
    hours: hours ?? this.hours,
  );
  @override
  List<Object?> get props => [faqs, phone, email, hours];
}
