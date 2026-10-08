import 'package:equatable/equatable.dart';

/// The sender's acknowledgement does not include another copy of the message.
class ChatMessageAcknowledgement extends Equatable {
  const ChatMessageAcknowledgement({
    required this.id,
    required this.clientMessageId,
    required this.status,
  });
  const ChatMessageAcknowledgement.initial()
    : id = '',
      clientMessageId = '',
      status = '';

  factory ChatMessageAcknowledgement.fromJson(Map<String, dynamic> json) =>
      ChatMessageAcknowledgement(
        id: json['id']?.toString() ?? '',
        clientMessageId: json['client_message_id']?.toString() ?? '',
        status: json['status']?.toString() ?? '',
      );

  final String id;
  final String clientMessageId;
  final String status;
  bool get isSent =>
      id.isNotEmpty && clientMessageId.isNotEmpty && status == 'sent';
  Map<String, dynamic> toJson() => {
    'id': id,
    'client_message_id': clientMessageId,
    'status': status,
  };
  ChatMessageAcknowledgement copyWith({
    String? id,
    String? clientMessageId,
    String? status,
  }) => ChatMessageAcknowledgement(
    id: id ?? this.id,
    clientMessageId: clientMessageId ?? this.clientMessageId,
    status: status ?? this.status,
  );
  @override
  List<Object?> get props => [id, clientMessageId, status];
}
