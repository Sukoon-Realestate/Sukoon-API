import 'package:flutter/material.dart';
import 'package:melos_core/config/res/config_imports.dart';

import '../widgets/chat_list/chat_list_content.dart';

class ChatListScreen extends StatelessWidget {
  const ChatListScreen({super.key});

  @override
  Widget build(BuildContext context) {
    return const Scaffold(
      backgroundColor: AppColors.scaffoldBackground,
      body: SafeArea(child: ChatListContent()),
    );
  }
}
