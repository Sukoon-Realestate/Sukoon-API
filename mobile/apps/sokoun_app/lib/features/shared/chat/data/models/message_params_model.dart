class MessageParamsModel {
  const MessageParamsModel({
    required this.conversationId,
    required this.content,
  });

  const MessageParamsModel.initial() : conversationId = '', content = '';

  final String conversationId;
  final String content;

  MessageParamsModel copyWith({String? conversationId, String? content}) {
    return MessageParamsModel(
      conversationId: conversationId ?? this.conversationId,
      content: content ?? this.content,
    );
  }

  Map<String, dynamic> toJson() => toSocketJson();

  Map<String, dynamic> toRestJson() => {'content': content};

  Map<String, dynamic> toSocketJson() => {
    'conversation_id': conversationId,
    'content': content,
  };
}
