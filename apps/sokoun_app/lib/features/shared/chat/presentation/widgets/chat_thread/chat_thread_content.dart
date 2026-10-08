import 'package:melos_core/core/widgets/app_text.dart';
import 'chat_recovered_messages.dart';
import '../chat_unavailable_indicator.dart';
import 'dart:async';

import 'package:flutter/material.dart';
import 'package:flutter_bloc/flutter_bloc.dart';
import 'package:melos_core/config/language/locale_keys.g.dart';
import 'package:melos_core/core/shared/models/user_models/user_model.dart';
import 'package:melos_core/core/widgets/chat_builder/chat_message.dart';
import 'package:melos_core/core/widgets/toast_messages/toast_message.dart';
import 'package:melos_core/core/shared/base_state.dart';
import 'package:pagify/pagify.dart';

import '../../../data/models/chat_content.dart';
import '../../../data/models/chat_socket_message.dart';
import '../../cubits/chat_thread_cubit.dart';
import 'chat_composer.dart';
import 'chat_messages_view.dart';
import 'chat_queued_messages_banner.dart';

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
  final ValueNotifier<bool> _isSending = ValueNotifier(false);
  bool _wasKeyboardOpen = false;
  bool _isNearLatestMessage = true;

  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addObserver(this);
    _chatController = PagifyController<ChatMessages>();
    _messageController = TextEditingController(
      text: context.read<ChatThreadCubit>().state.draft,
    );
    _messageController.addListener(_draftChanged);
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
    if (isKeyboardOpen && !_wasKeyboardOpen && _isNearLatestMessage) {
      _chatController.moveToMaxBottom();
    }
    _wasKeyboardOpen = isKeyboardOpen;
  }

  @override
  void dispose() {
    WidgetsBinding.instance.removeObserver(this);
    _keyboardMetricsTimer?.cancel();
    _messageController.removeListener(_draftChanged);
    _isSending.dispose();
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
    if (pendingMessageIndex >= 0) {
      _chatController.replaceWith(pendingMessageIndex, chatMessage);
    } else {
      final bool shouldScroll = _isNearLatestMessage;
      _chatController.addItem(chatMessage);
      if (shouldScroll) _chatController.moveToMaxBottom();
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
        name: content.sender.fullName,
        image: content.sender.avatarUrl,
        isFromMe: isFromMe,
      ),
      time: time,
      createdAt: createdAt,
      messageState: isFromMe ? MessageState.sent : MessageState.read,
    );
  }

  void _draftChanged() =>
      context.read<ChatThreadCubit>().updateDraft(_messageController.text);

  Future<void> _sendTextMessage() async {
    if (_isSending.value || !context.read<ChatThreadCubit>().canSend) return;
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
      createdAt: DateTime.now(),
      messageState: MessageState.pending,
    );
    _chatController.addItem(pendingMessage);
    _chatController.moveToMaxBottom();
    _isSending.value = true;
    try {
      final result = await _sendMessage(
        text,
        localMessageId: pendingMessage.message.id.toString(),
      );
      if (!mounted) return;
      if (result.isSent || result.isQueued) {
        if (_messageController.text.trim() == text) _messageController.clear();
      } else {
        _chatController.removeWhere(
          (item) => item.message.id == pendingMessage.message.id,
        );
      }
    } finally {
      if (mounted) _isSending.value = false;
    }
  }

  Future<ChatSendResult> _sendMessage(
    String text, {
    required String localMessageId,
  }) async {
    final ChatSendResult result = await context
        .read<ChatThreadCubit>()
        .sendTextMessage(text, localMessageId: localMessageId);
    if (!result.isSent && !result.isQueued && mounted) {
      Messages.showToast(
        msg: LocaleKeys.waitingForConnection,
        status: BaseStatus.error,
      );
    }
    return result;
  }

  @override
  Widget build(BuildContext context) {
    return MultiBlocListener(
      listeners: [
        BlocListener<ChatThreadCubit, ChatThreadState>(
          listenWhen: (previous, current) => previous.draft != current.draft,
          listener: (context, state) {
            if (_messageController.text != state.draft) {
              _messageController.value = TextEditingValue(
                text: state.draft,
                selection: TextSelection.collapsed(offset: state.draft.length),
              );
            }
          },
        ),
        BlocListener<ChatThreadCubit, ChatThreadState>(
          listenWhen: (previous, current) =>
              previous.receivedMessageRevision !=
              current.receivedMessageRevision,
          listener: (context, state) {
            final ChatSocketMessage? message = state.receivedMessage;
            if (message != null) {
              _receiveSocketMessage(
                message,
                localMessageId: state.confirmedLocalMessageId,
              );
            }
          },
        ),
        BlocListener<ChatThreadCubit, ChatThreadState>(
          listenWhen: (previous, current) =>
              previous.readReceiptRevision != current.readReceiptRevision,
          listener: (context, state) => _receiveReadReceipt(),
        ),
      ],
      child: Column(
        children: [
          const ChatQueuedMessagesBanner(),
          const ChatRecoveredMessages(),
          BlocSelector<ChatThreadCubit, ChatThreadState, bool>(
            selector: (state) => state.localSaveFailed,
            builder: (context, failed) => failed
                ? Padding(
                    padding: const EdgeInsets.all(8),
                    child: AppText(LocaleKeys.freeChatDraftSaveFailed),
                  )
                : const SizedBox.shrink(),
          ),
          Expanded(
            child: NotificationListener<ScrollNotification>(
              onNotification: (notification) {
                if (notification.depth == 0) {
                  _isNearLatestMessage = notification.metrics.extentAfter <= 80;
                }
                return false;
              },
              child: ChatMessagesView(
                conversation: widget.conversation,
                controller: _chatController,
                initialMessagesRequest: widget.initialMessagesRequest,
                messagesCacheKey: widget.messagesCacheKey,
              ),
            ),
          ),
          if (widget.conversation.canSend == false)
            ChatUnavailableIndicator(
              message: LocaleKeys.freeChatUnavailable,
              icon: Icons.lock_outline,
            )
          else
            ValueListenableBuilder<bool>(
              valueListenable: _isSending,
              builder: (context, sending, _) => AbsorbPointer(
                absorbing: sending,
                child: ChatComposer(
                  controller: _messageController,
                  onSendPressed: _sendTextMessage,
                ),
              ),
            ),
        ],
      ),
    );
  }
}
