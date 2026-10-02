import 'package:flutter/material.dart';
import 'package:melos_core/core/navigation/navigator.dart';

import '../../data/models/chat_content.dart';
import '../screens/chat_restricted_screen.dart';
import '../screens/chat_screen.dart';
import '../screens/previous_chat_screen.dart';
import 'chat_card.dart';

class ChatListTile extends StatelessWidget {
  const ChatListTile({
    super.key,
    required this.conversation,
    this.isReadOnly = false,
    this.onOpen,
  });

  final ConversationContent conversation;
  final bool isReadOnly;
  final VoidCallback? onOpen;

  void _openConversation() {
    onOpen?.call();
    if (isReadOnly) {
      Go.to(PreviousChatScreen(conversation: conversation));
      return;
    }
    if (conversation.isVerified) {
      Go.to(ChatScreen(conversation: conversation));
      return;
    }
    Go.to(ChatRestrictedScreen(conversation: conversation));
  }

  @override
  Widget build(BuildContext context) {
    return InkWell(
      onTap: _openConversation,
      child: ChatCard(conversation: conversation),
    );
  }
}
