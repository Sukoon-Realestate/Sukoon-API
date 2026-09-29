import 'package:sokoun_app/shared_widgets/app_scaffold.dart';
import 'package:flutter/material.dart';
import 'package:melos_core/config/res/config_imports.dart';

import '../../data/models/chat_content.dart';
import '../widgets/chat_restricted/chat_disabled_composer.dart';
import '../widgets/chat_restricted/chat_restricted_content.dart';
import '../widgets/chat_restricted/chat_restricted_header.dart';

class ChatRestrictedScreen extends StatelessWidget {
  const ChatRestrictedScreen({super.key, required this.conversation});

  final ConversationContent conversation;

  @override
  Widget build(BuildContext context) {
    return AppScaffold(
      showBackButton: false,
      backgroundColor: AppColors.scaffoldBackground,
      body: SafeArea(
        bottom: false,
        child: Column(
          children: [
            ChatRestrictedHeader(conversation: conversation),
            const Expanded(child: ChatRestrictedContent()),
            const ChatDisabledComposer(),
          ],
        ),
      ),
    );
  }
}
