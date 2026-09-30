import 'package:flutter/material.dart';
import 'package:melos_core/config/language/locale_keys.g.dart';
import 'package:sokoun_app/shared_widgets/app_scaffold.dart';

import '../widgets/chat_list/chat_list_content.dart';

class ChatsScreen extends StatelessWidget {
  const ChatsScreen({super.key});

  @override
  Widget build(BuildContext context) => AppScaffold(
    title: LocaleKeys.chatConversationsTitle,
    body: const SafeArea(child: ChatListContent()),
  );
}

class ChatListScreen extends ChatsScreen {
  const ChatListScreen({super.key});
}
