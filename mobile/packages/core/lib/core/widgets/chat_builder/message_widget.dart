import 'package:flutter/material.dart';

import 'chat_message.dart';


class MessageWidget extends StatelessWidget {
  final ChatMessages message;
  final Widget Function(ChatMessages message) rightMessageBuilder;
  final Widget Function(ChatMessages message) leftMessageBuilder;

  const MessageWidget({super.key,
    required this.message,
    required this.rightMessageBuilder,
    required this.leftMessageBuilder,
  });

  @override
  Widget build(BuildContext context) {
    return message.sender.isFromMe?
    rightMessageBuilder(message) :
    leftMessageBuilder(message);
  }
}