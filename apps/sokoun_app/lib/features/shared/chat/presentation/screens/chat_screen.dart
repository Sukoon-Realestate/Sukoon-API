import 'package:sokoun_app/features/shared/rental_offers/data/models/rental_selection.dart';
import 'package:sokoun_app/features/shared/rental_offers/presentation/widgets/rental_offer_labels.dart';
import 'package:melos_core/config/language/locale_keys.g.dart';
import 'package:melos_core/core/widgets/app_text.dart';
import '../widgets/report/chat_report_button.dart';
import '../widgets/chat/chat_participant_title.dart';
import 'package:sokoun_app/shared_widgets/app_scaffold.dart';

import 'package:flutter/material.dart';
import 'package:flutter_bloc/flutter_bloc.dart';
import 'package:melos_core/config/res/config_imports.dart';

import '../../data/chat_unread_refresh_bus.dart';
import '../../data/chat_thread_data.dart';
import '../../data/models/chat_content.dart';
import '../cubits/chat_thread_cubit.dart';
import '../widgets/chat_thread/chat_thread_content.dart';

class ChatScreen extends StatefulWidget {
  const ChatScreen({super.key, required this.conversation, this.rentalContext});
  final RentalSelection? rentalContext;

  final ConversationContent conversation;

  @override
  State<ChatScreen> createState() => _ChatScreenState();
}

class _ChatScreenState extends State<ChatScreen> with WidgetsBindingObserver {
  late final ChatThreadCubit _chatThreadCubit;
  late final ChatThreadData _chatThreadData;
  late final Future<List<ChatMessageContent>> _initialMessagesRequest;

  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addObserver(this);
    _chatThreadCubit = ChatThreadCubit(
      conversationId: widget.conversation.id,
      canSend: widget.conversation.canSend != false,
      otherParticipantId: widget.conversation.otherParticipant.id,
      initialContact: widget.conversation.otherParticipant,
    );
    _chatThreadData = ChatThreadData(conversationId: widget.conversation.id);
    _initialMessagesRequest = _initializeChat();
    _chatThreadCubit.refreshContact();
    ChatUnreadRefreshBus.requestRefresh(
      removedUnreadCount: widget.conversation.unreadCount,
    );
  }

  Future<List<ChatMessageContent>> _initializeChat() async {
    late final List<ChatMessageContent> initialMessages;
    await Future.wait<void>([
      _chatThreadData.loadInitialMessages().then<void>((messages) {
        initialMessages = messages;
      }),
      _chatThreadCubit.connect(),
    ]);
    return initialMessages;
  }

  @override
  void didChangeAppLifecycleState(AppLifecycleState state) {
    _chatThreadCubit.onAppLifecycleStateChanged(state);
    if (state == AppLifecycleState.resumed) _chatThreadCubit.refreshContact();
  }

  @override
  void dispose() {
    WidgetsBinding.instance.removeObserver(this);
    _chatThreadCubit.close();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return BlocProvider<ChatThreadCubit>.value(
      value: _chatThreadCubit,
      child: AppScaffold(
        titleWidget: ChatParticipantTitle(conversation: widget.conversation),
        showBackButton: true,
        toolbarHeight: 56 + MediaQuery.textScalerOf(context).scale(16),
        actions: [ChatReportButton(conversation: widget.conversation)],
        backgroundColor: context.appColor(
          AppColors.scaffoldBackground,
          surface: true,
        ),
        resizeToAvoidBottomInset: true,
        body: SafeArea(
          bottom: false,
          child: Column(
            children: [
              if (widget.rentalContext != null)
                ExpansionTile(
                  title: AppText(
                    LocaleKeys.rentalChatContext.replaceAll(
                      '{offer}',
                      RentalOfferLabels.accommodation(widget.rentalContext!),
                    ),
                  ),
                  children: [AppText(LocaleKeys.rentalChatContextHelp)],
                ),
              Expanded(
                child:
                    BlocSelector<
                      ChatThreadCubit,
                      ChatThreadState,
                      ChatParticipantContent
                    >(
                      selector: (state) => state.contact,
                      builder: (context, contact) => ChatThreadContent(
                        conversation: widget.conversation.copyWith(
                          otherParticipant: contact,
                        ),
                        initialMessagesRequest: _initialMessagesRequest,
                        messagesCacheKey: _chatThreadData.messagesCacheKey,
                      ),
                    ),
              ),
            ],
          ),
        ),
      ),
    );
  }
}
