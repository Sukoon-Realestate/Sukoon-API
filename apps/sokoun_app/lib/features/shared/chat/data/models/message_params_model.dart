class MessageParamsModel {
  const MessageParamsModel({
    required this.conversationId,
    required this.content,
    this.clientMessageId = '',
  });

  const MessageParamsModel.initial()
    : conversationId = '',
      content = '',
      clientMessageId = '';

  final String conversationId;
  final String content;
  final String clientMessageId;

  MessageParamsModel copyWith({
    String? conversationId,
    String? content,
    String? clientMessageId,
  }) {
    return MessageParamsModel(
      conversationId: conversationId ?? this.conversationId,
      content: content ?? this.content,
      clientMessageId: clientMessageId ?? this.clientMessageId,
    );
  }

  Map<String, dynamic> toJson() => toSocketJson();

  Map<String, dynamic> toRestJson() => {
    'content': content,
    if (clientMessageId.isNotEmpty) 'client_message_id': clientMessageId,
  };

  Map<String, dynamic> toSocketJson() => {
    'conversation_id': conversationId,
    'content': content,
    if (clientMessageId.isNotEmpty) 'client_message_id': clientMessageId,
  };
}
