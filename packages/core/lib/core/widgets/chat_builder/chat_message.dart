enum MessageState { pending, sent, delivered, read }

class Message {
  final Object id;
  final String body;
  final String type;

  Message({required this.id, required this.type, required this.body});
}

class Sender {
  final String id;
  final String name;
  final String image;
  final bool isFromMe;

  Sender({
    required this.id,
    required this.name,
    required this.image,
    required this.isFromMe,
  });
}

class ChatMessages {
  final Message message;
  final Sender sender;
  String? time;
  MessageState? messageState;

  ChatMessages({
    required this.message,
    required this.sender,
    this.time,
    this.messageState,
  });
}
