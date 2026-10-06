import 'package:equatable/equatable.dart';
import '../support_json.dart';
import '../enums/support_ticket_state.dart';

class SupportAttachment extends Equatable {
  const SupportAttachment({
    required this.id,
    required this.name,
    required this.url,
  });
  const SupportAttachment.initial() : id = '', name = '', url = '';
  factory SupportAttachment.fromJson(Map<String, dynamic> json) =>
      SupportAttachment(
        id: json['id']?.toString() ?? '',
        name: json['name']?.toString() ?? '',
        url: json['url']?.toString() ?? '',
      );
  final String id;
  final String name;
  final String url;
  Map<String, dynamic> toJson() => {'id': id, 'name': name, 'url': url};
  SupportAttachment copyWith({String? id, String? name, String? url}) =>
      SupportAttachment(
        id: id ?? this.id,
        name: name ?? this.name,
        url: url ?? this.url,
      );
  @override
  List<Object?> get props => [id, name, url];
}

class SupportMessage extends Equatable {
  const SupportMessage({
    required this.id,
    required this.sender,
    required this.body,
    required this.createdAt,
    required this.attachments,
  });
  const SupportMessage.initial()
    : id = '',
      sender = 'user',
      body = '',
      createdAt = '',
      attachments = const [];
  factory SupportMessage.fromJson(Map<String, dynamic> json) => SupportMessage(
    id: json['id']?.toString() ?? '',
    sender: json['sender']?.toString() ?? 'user',
    body: json['body']?.toString() ?? '',
    createdAt: json['created_at']?.toString() ?? '',
    attachments: supportList(json['attachments'], SupportAttachment.fromJson),
  );
  final String id;
  final String sender;
  final String body;
  final String createdAt;
  final List<SupportAttachment> attachments;
  bool get isFromUser => sender == 'user';
  Map<String, dynamic> toJson() => {
    'id': id,
    'sender': sender,
    'body': body,
    'created_at': createdAt,
    'attachments': attachments.map((item) => item.toJson()).toList(),
  };
  SupportMessage copyWith({
    String? id,
    String? sender,
    String? body,
    String? createdAt,
    List<SupportAttachment>? attachments,
  }) => SupportMessage(
    id: id ?? this.id,
    sender: sender ?? this.sender,
    body: body ?? this.body,
    createdAt: createdAt ?? this.createdAt,
    attachments: attachments ?? this.attachments,
  );
  @override
  List<Object?> get props => [id, sender, body, createdAt, attachments];
}

class SupportTicketContent extends Equatable {
  const SupportTicketContent({
    required this.id,
    required this.reference,
    required this.subject,
    required this.status,
    required this.createdAt,
    required this.messages,
  });
  const SupportTicketContent.initial()
    : id = '',
      reference = '',
      subject = '',
      status = SupportTicketState.unknown,
      createdAt = '',
      messages = const [];
  factory SupportTicketContent.fromJson(Map<String, dynamic> json) =>
      SupportTicketContent(
        id: json['id']?.toString() ?? '',
        reference: json['reference']?.toString() ?? '',
        subject: json['subject']?.toString() ?? '',
        status: SupportTicketState.fromJson(json['status']),
        createdAt: json['created_at']?.toString() ?? '',
        messages: supportList(json['messages'], SupportMessage.fromJson),
      );
  final String id;
  final String reference;
  final String subject;
  final SupportTicketState status;
  final String createdAt;
  final List<SupportMessage> messages;
  bool get isResolved => status.isResolved;
  bool get isWaiting => status == SupportTicketState.inProgress;
  bool get canReply => id.isNotEmpty && status.canReply;
  Map<String, dynamic> toJson() => {
    'id': id,
    'reference': reference,
    'subject': subject,
    'status': status.code,
    'created_at': createdAt,
    'messages': messages.map((item) => item.toJson()).toList(),
  };
  SupportTicketContent copyWith({
    String? id,
    String? reference,
    String? subject,
    SupportTicketState? status,
    String? createdAt,
    List<SupportMessage>? messages,
  }) => SupportTicketContent(
    id: id ?? this.id,
    reference: reference ?? this.reference,
    subject: subject ?? this.subject,
    status: status ?? this.status,
    createdAt: createdAt ?? this.createdAt,
    messages: messages ?? this.messages,
  );
  @override
  List<Object?> get props => [
    id,
    reference,
    subject,
    status,
    createdAt,
    messages,
  ];
}
