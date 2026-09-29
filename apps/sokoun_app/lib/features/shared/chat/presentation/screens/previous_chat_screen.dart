import '../widgets/chat/chat_participant_title.dart';
import 'package:sokoun_app/shared_widgets/app_scaffold.dart';
import 'package:flutter/material.dart';
import 'package:melos_core/config/res/config_imports.dart';
import 'package:melos_core/core/widgets/chat_builder/chat_message.dart';
import 'package:pagify/pagify.dart';

import '../../data/chat_thread_data.dart';
import '../../data/models/chat_content.dart';
import '../widgets/chat/chat_view.dart';

/// Read-only history: no socket connection and no composer.
class PreviousChatScreen extends StatefulWidget {
  const PreviousChatScreen({super.key, required this.conversation});

  final ConversationContent conversation;

  @override
  State<PreviousChatScreen> createState() => _PreviousChatScreenState();
}

class _PreviousChatScreenState extends State<PreviousChatScreen> {
  late final ChatThreadData _chatThreadData;
  late final PagifyController<ChatMessages> _chatController;
  late final Future<List<ChatMessageContent>> _initialMessagesRequest;

  @override
  void initState() {
    super.initState();
    _chatThreadData = ChatThreadData(conversationId: widget.conversation.id);
    _chatController = PagifyController<ChatMessages>();
    _initialMessagesRequest = _chatThreadData.loadInitialMessages();
  }

  @override
  Widget build(BuildContext context) {
    return AppScaffold(
      titleWidget: ChatParticipantTitle(conversation: widget.conversation),
      showBackButton: true,
      toolbarHeight: 56 + MediaQuery.textScalerOf(context).scale(16),
      backgroundColor: AppColors.scaffoldBackground,
      body: SafeArea(
        bottom: false,
        child: ChatView(
          conversation: widget.conversation,
          controller: _chatController,
          initialMessagesRequest: _initialMessagesRequest,
          messagesCacheKey: _chatThreadData.messagesCacheKey,
        ),
      ),
    );
  }
}
