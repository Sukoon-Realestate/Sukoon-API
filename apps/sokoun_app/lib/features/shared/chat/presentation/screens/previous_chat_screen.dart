import '../widgets/chat/chat_participant_title.dart';
import 'package:sokoun_app/shared_widgets/app_scaffold.dart';
import 'package:flutter/material.dart';
import 'package:flutter_bloc/flutter_bloc.dart';
import 'package:melos_core/config/res/config_imports.dart';
import 'package:melos_core/core/widgets/chat_builder/chat_message.dart';
import 'package:pagify/pagify.dart';

import '../../data/chat_thread_data.dart';
import '../../data/models/chat_content.dart';
import '../../../contact/presentation/widgets/visit_contact_refresh.dart';
import '../cubits/chat_thread_cubit.dart';
import '../widgets/chat_thread/chat_messages_view.dart';

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
  late final ChatThreadCubit _contactCubit;

  @override
  void initState() {
    super.initState();
    _contactCubit = ChatThreadCubit(
      conversationId: widget.conversation.id,
      otherParticipantId: widget.conversation.otherParticipant.id,
      initialContact: widget.conversation.otherParticipant,
      readOnly: true,
    );
    _contactCubit.refreshContact();
    _chatThreadData = ChatThreadData(conversationId: widget.conversation.id);
    _chatController = PagifyController<ChatMessages>();
    _initialMessagesRequest = _chatThreadData.loadInitialMessages();
  }

  @override
  void dispose() {
    _contactCubit.close();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return AppScaffold(
      titleWidget: ChatParticipantTitle(conversation: widget.conversation),
      showBackButton: true,
      toolbarHeight: 56 + MediaQuery.textScalerOf(context).scale(16),
      backgroundColor: context.appColor(
        AppColors.scaffoldBackground,
        surface: true,
      ),
      body: VisitContactRefresh(
        onRefresh: () =>
            _contactCubit.refreshContact(afterVisitAcceptance: true),
        child: SafeArea(
          bottom: false,
          child:
              BlocSelector<
                ChatThreadCubit,
                ChatThreadState,
                ChatParticipantContent
              >(
                bloc: _contactCubit,
                selector: (state) => state.contact,
                builder: (context, contact) => ChatMessagesView(
                  conversation: widget.conversation.copyWith(
                    otherParticipant: contact,
                  ),
                  controller: _chatController,
                  initialMessagesRequest: _initialMessagesRequest,
                  messagesCacheKey: _chatThreadData.messagesCacheKey,
                ),
              ),
        ),
      ),
    );
  }
}
