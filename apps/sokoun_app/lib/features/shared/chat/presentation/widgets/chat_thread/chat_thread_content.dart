import 'dart:async';

import 'package:flutter/material.dart';
import 'package:flutter_bloc/flutter_bloc.dart';
import 'package:melos_core/config/language/locale_keys.g.dart';
import 'package:melos_core/config/res/config_imports.dart';
import 'package:melos_core/core/navigation/navigator.dart';
import 'package:melos_core/core/shared/models/user_models/user_model.dart';
import 'package:melos_core/core/widgets/chat_builder/chat_message.dart';
import 'package:melos_core/core/widgets/toast_messages/custom_messages.dart';
import 'package:pagify/pagify.dart';

import '../../../data/models/chat_content.dart';
import '../../../data/models/chat_socket_message.dart';
import '../../cubits/socket_cubit.dart';
import '../../screens/chats_screen.dart';
import '../chat/bottom_bar.dart';
import '../chat/chat_view.dart';
import '../chat/upper_view.dart';
import '../report/chat_report_sheet.dart';

class ChatThreadContent extends StatefulWidget {
  const ChatThreadContent({
    super.key,
    required this.conversation,
    required this.initialMessagesRequest,
    required this.messagesCacheKey,
  });

  final ConversationContent conversation;
  final Future<List<ChatMessageContent>> initialMessagesRequest;
  final String? messagesCacheKey;

  @override
  State<ChatThreadContent> createState() => _ChatThreadContentState();
}

class _ChatThreadContentState extends State<ChatThreadContent>
    with WidgetsBindingObserver {
  late final PagifyController<ChatMessages> _chatController;
  late final TextEditingController _messageController;
  Timer? _keyboardMetricsTimer;
  bool _wasKeyboardOpen = false;

  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addObserver(this);
    _chatController = PagifyController<ChatMessages>();
    _messageController = TextEditingController();
  }

  @override
  void didChangeMetrics() {
    _keyboardMetricsTimer?.cancel();
    _keyboardMetricsTimer = Timer(
      const Duration(milliseconds: 100),
      _handleKeyboardMetricsSettled,
    );
  }

  void _handleKeyboardMetricsSettled() {
    if (!mounted) return;

    final bool isKeyboardOpen = MediaQuery.viewInsetsOf(context).bottom > 0;
    if (isKeyboardOpen && !_wasKeyboardOpen) {
      _chatController.moveToMaxBottom();
    }
    _wasKeyboardOpen = isKeyboardOpen;
  }

  @override
  void dispose() {
    WidgetsBinding.instance.removeObserver(this);
    _keyboardMetricsTimer?.cancel();
    _messageController.dispose();
    super.dispose();
  }

  Future<void> _receiveSocketMessage(
    ChatSocketMessage message, {
    String? localMessageId,
  }) async {
    if (!mounted) return;

    final ChatMessages chatMessage = _toSocketChatMessage(message);
    final List<ChatMessages> currentMessages = _chatController.items;
    final int serverMessageIndex = currentMessages.indexWhere(
      (item) => item.message.id == message.id,
    );
    if (serverMessageIndex >= 0) {
      _chatController.replaceWith(serverMessageIndex, chatMessage);
      return;
    }

    int pendingMessageIndex = localMessageId == null
        ? -1
        : currentMessages.indexWhere(
            (item) => item.message.id.toString() == localMessageId,
          );
    if (pendingMessageIndex < 0) {
      pendingMessageIndex = currentMessages.indexWhere(
        (item) =>
            chatMessage.sender.isFromMe &&
            item.sender.isFromMe &&
            item.messageState == MessageState.pending &&
            item.message.body == message.content,
      );
    }
    if (pendingMessageIndex >= 0) {
      _chatController.replaceWith(pendingMessageIndex, chatMessage);
    } else {
      _chatController.addItem(chatMessage);
      _chatController.moveToMaxBottom();
    }

    if (!chatMessage.sender.isFromMe) {
      await context.read<ChatThreadCubit>().markConversationAsRead();
    }
  }

  Future<void> _receiveReadReceipt() async {
    for (final ChatMessages message in _chatController.items) {
      if (message.sender.isFromMe) {
        message.messageState = MessageState.read;
      }
    }
    await _chatController.reload();
  }

  ChatMessages _toSocketChatMessage(ChatSocketMessage content) {
    final bool isFromMe = content.isFromMe;
    final DateTime? createdAt = content.createdAt?.toLocal();
    final String time = createdAt == null
        ? LocaleKeys.chatNow
        : MaterialLocalizations.of(
            context,
          ).formatTimeOfDay(TimeOfDay.fromDateTime(createdAt));

    return ChatMessages(
      message: Message(id: content.id, type: 'text', body: content.content),
      sender: Sender(
        id: content.sender.id,
        name: content.sender.name,
        image: content.sender.avatarUrl,
        isFromMe: isFromMe,
      ),
      time: time,
      messageState: isFromMe ? MessageState.sent : MessageState.read,
    );
  }

  void _sendTextMessage() {
    final String text = _messageController.text.trim();
    if (text.isEmpty) return;

    final ChatMessages pendingMessage = ChatMessages(
      message: Message(
        id: 'local-${DateTime.now().microsecondsSinceEpoch}',
        type: 'text',
        body: text,
      ),
      sender: Sender(
        id: UserModel.currentUser?.id ?? '',
        name: UserModel.currentUser?.name ?? '',
        image: '',
        isFromMe: true,
      ),
      time: LocaleKeys.chatNow,
      messageState: MessageState.pending,
    );
    _chatController.addItem(pendingMessage);
    _chatController.moveToMaxBottom();
    _messageController.clear();
    unawaited(
      _sendMessage(text, localMessageId: pendingMessage.message.id.toString()),
    );
  }

  Future<void> _sendMessage(
    String text, {
    required String localMessageId,
  }) async {
    final ChatSendResult result = await context
        .read<ChatThreadCubit>()
        .sendTextMessage(text, localMessageId: localMessageId);
    if (!result.isSent && !result.isQueued && mounted) {
      MessageUtils.showSnackBar(
        LocaleKeys.waitingForConnection,
        context: context,
      );
    }
  }

  Future<void> _showReportSheet() async {
    final bool? submitted = await showModalBottomSheet<bool>(
      context: context,
      isScrollControlled: true,
      useSafeArea: true,
      backgroundColor: AppColors.transparent,
      barrierColor: AppColors.blackAlpha50,
      builder: (context) => const ChatReportSheet(),
    );

    if (submitted == true && mounted) {
      Go.off(const ChatListScreen());
    }
  }

  @override
  Widget build(BuildContext context) {
    return MultiBlocListener(
      listeners: [
        BlocListener<ChatThreadCubit, ChatThreadState>(
          listenWhen: (previous, current) =>
              previous.receivedMessageRevision !=
              current.receivedMessageRevision,
          listener: (context, state) {
            final ChatSocketMessage? message = state.receivedMessage;
            if (message != null) {
              unawaited(
                _receiveSocketMessage(
                  message,
                  localMessageId: state.confirmedLocalMessageId,
                ),
              );
            }
          },
        ),
        BlocListener<ChatThreadCubit, ChatThreadState>(
          listenWhen: (previous, current) =>
              previous.readReceiptRevision != current.readReceiptRevision,
          listener: (context, state) => unawaited(_receiveReadReceipt()),
        ),
      ],
      child: Column(
        children: [
          ChatUpperWidget(
            conversation: widget.conversation,
            onReportPressed: _showReportSheet,
          ),
          Expanded(
            child: ChatView(
              conversation: widget.conversation,
              controller: _chatController,
              initialMessagesRequest: widget.initialMessagesRequest,
              messagesCacheKey: widget.messagesCacheKey,
            ),
          ),
          ChatBottomBar(
            controller: _messageController,
            onSendPressed: _sendTextMessage,
          ),
        ],
      ),
    );
  }
}
