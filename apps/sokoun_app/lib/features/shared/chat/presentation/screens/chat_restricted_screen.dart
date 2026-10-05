import '../widgets/chat/chat_participant_title.dart';
import 'package:sokoun_app/shared_widgets/app_scaffold.dart';
import 'package:flutter/material.dart';
import 'package:melos_core/config/res/config_imports.dart';

import '../../data/models/chat_content.dart';
import '../widgets/chat_restricted/chat_disabled_composer.dart';
import '../widgets/chat_restricted/chat_restricted_content.dart';

class ChatRestrictedScreen extends StatelessWidget {
  const ChatRestrictedScreen({super.key, required this.conversation});

  final ConversationContent conversation;

  @override
  Widget build(BuildContext context) {
    return AppScaffold(
      titleWidget: ChatParticipantTitle(conversation: conversation),
      showBackButton: true,
      toolbarHeight: 56 + MediaQuery.textScalerOf(context).scale(16),
      backgroundColor: context.appColor(
        AppColors.scaffoldBackground,
        surface: true,
      ),
      body: SafeArea(
        bottom: false,
        child: Column(
          children: [
            const Expanded(child: ChatRestrictedContent()),
            const ChatDisabledComposer(),
          ],
        ),
      ),
    );
  }
}
