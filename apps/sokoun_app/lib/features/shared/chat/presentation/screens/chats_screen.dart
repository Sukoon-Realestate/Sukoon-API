import 'package:sokoun_app/shared_widgets/app_scaffold.dart';
import 'package:flutter/material.dart';
import 'package:melos_core/config/res/config_imports.dart';

import '../widgets/chat_list/chat_list_content.dart';

class ChatsScreen extends StatelessWidget {
  const ChatsScreen({super.key});

  @override
  Widget build(BuildContext context) {
    return const AppScaffold(
      showBackButton: false,
      backgroundColor: AppColors.scaffoldBackground,
      body: SafeArea(child: ChatListContent()),
    );
  }
}

/// Backwards-compatible name used by existing navigation call sites.
class ChatListScreen extends ChatsScreen {
  const ChatListScreen({super.key});
}
