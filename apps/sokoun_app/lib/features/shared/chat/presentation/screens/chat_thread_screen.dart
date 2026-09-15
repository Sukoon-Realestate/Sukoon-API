import 'dart:async';

import 'package:flutter/material.dart';
import 'package:flutter_bloc/flutter_bloc.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';
import 'package:melos_core/config/language/locale_keys.g.dart';
import 'package:melos_core/config/res/config_imports.dart';
import 'package:melos_core/core/extensions/padding_extension.dart';
import 'package:melos_core/core/navigation/navigator.dart';
import 'package:melos_core/core/shared/models/user_models/user_model.dart';
import 'package:melos_core/core/widgets/app_text.dart';
import 'package:melos_core/core/widgets/chat_builder/chat_message.dart';
import 'package:melos_core/core/widgets/chat_builder/easy_chat.dart';
import 'package:melos_core/core/widgets/toast_messages/custom_messages.dart';
import 'package:pagify/helpers/data_and_pagination_data.dart';
import 'package:pagify/helpers/errors.dart';
import 'package:pagify/pagify.dart';
import 'package:sokoun_app/features/shared/chat/data/chat_data.dart';
import 'package:sokoun_app/features/shared/chat/data/chat_unread_refresh_bus.dart';
import 'package:sokoun_app/features/shared/chat/data/enums/chat_attachment_type.dart';
import 'package:sokoun_app/features/shared/chat/data/models/chat_content.dart';
import 'package:sokoun_app/features/shared/chat/data/models/chat_socket_message.dart';
import 'package:sokoun_app/features/shared/chat/presentation/cubits/chat_thread_cubit.dart';

import '../widgets/imports.dart';
import 'chat_list_screen.dart';

class ChatThreadScreen extends StatefulWidget {
  const ChatThreadScreen({super.key, required this.conversation});

  final ConversationContent conversation;

  @override
  State<ChatThreadScreen> createState() => _ChatThreadScreenState();
}

class _ChatThreadScreenState extends State<ChatThreadScreen>
    with WidgetsBindingObserver {
  late final PagifyController<ChatMessages> _chatController;
  late final TextEditingController _messageController;
  late final ChatThreadCubit _chatThreadCubit;
  PaginationData _messagePagination = PaginationData(
    perPage: ChatData.messagesPageSize,
    totalPages: 1,
  );
  int _nextMessageId = 100;
  bool _isRecording = false;

  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addObserver(this);
    _chatController = PagifyController<ChatMessages>();
    _messageController = TextEditingController();
    _chatThreadCubit = ChatThreadCubit(
      conversationId: widget.conversation.id.toString(),
    );
    ChatUnreadRefreshBus.requestRefresh(
      removedUnreadCount: widget.conversation.unreadCount,
    );
    unawaited(_chatThreadCubit.connect());
  }

  @override
  void dispose() {
    WidgetsBinding.instance.removeObserver(this);
    unawaited(_chatThreadCubit.close());
    _messageController.dispose();
    super.dispose();
  }

  @override
  void didChangeAppLifecycleState(AppLifecycleState state) {
    unawaited(_chatThreadCubit.onAppLifecycleStateChanged(state));
  }

  Future<void> _receiveSocketMessage(ChatSocketMessage message) async {
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

    final int pendingMessageIndex = currentMessages.indexWhere(
      (item) =>
          chatMessage.sender.isFromMe &&
          item.sender.isFromMe &&
          item.messageState == MessageState.pending &&
          item.message.body == message.content,
    );
    if (pendingMessageIndex >= 0) {
      _chatController.replaceWith(pendingMessageIndex, chatMessage);
    } else {
      _chatController.addAtBeginning(chatMessage);
    }

    if (!chatMessage.sender.isFromMe) {
      await _chatThreadCubit.markConversationAsRead();
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
    final String currentUserId = UserModel.currentUser?.id.toString() ?? '';
    final bool isFromMe =
        currentUserId.isNotEmpty && content.sender.id == currentUserId;
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

  Future<List<ChatMessageContent>> _loadMessages(
    BuildContext context,
    int currentPage,
  ) async {
    if (widget.conversation.id is int) {
      _messagePagination = PaginationData(
        perPage: ChatContent.initialMessages.length,
        totalPages: 1,
      );
      return currentPage == 1 ? ChatContent.initialMessages : const [];
    }

    final (List<ChatMessageContent>, PaginationData) page =
        await ChatData.getMessagesPage(
          conversationId: widget.conversation.id.toString(),
          page: currentPage,
        );
    _messagePagination = page.$2;
    return page.$1;
  }

  PagifyData<ChatMessages> _mapMessages(List<ChatMessageContent> response) {
    return PagifyData(
      data: response.reversed.map(_toChatMessage).toList(growable: false),
      paginationData: _messagePagination,
    );
  }

  ChatMessages _toChatMessage(ChatMessageContent content) {
    final String currentUserId = UserModel.currentUser?.id ?? '';
    final bool isFromMe = content.sender.id.isNotEmpty
        ? content.sender.id == currentUserId
        : content.isFromMe;
    final DateTime? createdAt = content.createdAt?.toLocal();
    final String messageTime = createdAt == null
        ? content.time
        : MaterialLocalizations.of(
            context,
          ).formatTimeOfDay(TimeOfDay.fromDateTime(createdAt));
    return ChatMessages(
      message: Message(id: content.id, type: content.type, body: content.body),
      sender: Sender(
        id: content.sender.id.isNotEmpty
            ? content.sender.id
            : isFromMe
            ? 'current-user'
            : '${widget.conversation.id}',
        name: content.sender.fullName.isNotEmpty
            ? content.sender.fullName
            : isFromMe
            ? 'current-user'
            : widget.conversation.name,
        image: content.sender.avatarUrl,
        isFromMe: isFromMe,
      ),
      time: messageTime,
      messageState: MessageState.read,
    );
  }

  void _sendTextMessage() {
    final String text = _messageController.text.trim();
    if (text.isEmpty) {
      return;
    }

    final ChatMessages pendingMessage = _buildOutgoingMessage(
      body: text,
      type: 'text',
      messageState: MessageState.pending,
    );
    _chatController.addAtBeginning(pendingMessage);
    _messageController.clear();
    FocusScope.of(context).unfocus();
    unawaited(_sendSocketMessage(text));
  }

  Future<void> _sendSocketMessage(String text) async {
    final ChatSendResult result = await _chatThreadCubit.sendTextMessage(text);
    final ChatSocketMessage? restMessage = result.restMessage;
    if (restMessage != null) await _receiveSocketMessage(restMessage);
    if (!result.isSent && mounted) {
      MessageUtils.showSnackBar(
        LocaleKeys.waitingForConnection,
        context: context,
      );
    }
  }

  Map<String, dynamic> _chatMessageToJson(ChatMessages item) => {
    'id': item.message.id,
    'body': item.message.body,
    'type': item.message.type,
    'sender_id': item.sender.id,
    'sender_name': item.sender.name,
    'sender_image': item.sender.image,
    'is_from_me': item.sender.isFromMe,
    'time': item.time,
    'message_state': item.messageState?.name,
  };

  ChatMessages _chatMessageFromJson(Map<String, dynamic> json) {
    final String stateName = json['message_state']?.toString() ?? '';
    return ChatMessages(
      message: Message(
        id: json['id'] ?? '',
        type: json['type']?.toString() ?? 'text',
        body: json['body']?.toString() ?? '',
      ),
      sender: Sender(
        id: json['sender_id']?.toString() ?? '',
        name: json['sender_name']?.toString() ?? '',
        image: json['sender_image']?.toString() ?? '',
        isFromMe: json['is_from_me'] == true,
      ),
      time: json['time']?.toString(),
      messageState: MessageState.values
          .where((state) => state.name == stateName)
          .firstOrNull,
    );
  }

  void _startVoiceRecording() => setState(() => _isRecording = true);

  void _cancelVoiceRecording() => setState(() => _isRecording = false);
  void _sendVoiceMessage() {
    _chatController.addAtBeginning(
      _buildOutgoingMessage(body: '0:08', type: 'voice'),
    );
    setState(() => _isRecording = false);
  }

  ChatMessages _buildOutgoingMessage({
    required String body,
    required String type,
    MessageState messageState = MessageState.sent,
  }) {
    _nextMessageId++;
    return ChatMessages(
      message: Message(id: _nextMessageId, type: type, body: body),
      sender: Sender(
        id: 'current-user',
        name: 'current-user',
        image: '',
        isFromMe: true,
      ),
      time: LocaleKeys.chatNow,
      messageState: messageState,
    );
  }

  Future<void> _showAttachments() async {
    await showModalBottomSheet<void>(
      context: context,
      isScrollControlled: true,
      useSafeArea: true,
      backgroundColor: AppColors.transparent,
      barrierColor: AppColors.blackAlpha50,
      builder: (context) {
        return ChatAttachmentsSheet(onAttachmentSelected: _selectAttachment);
      },
    );
  }

  void _selectAttachment(ChatAttachmentType type) {
    Go.back();
    _chatController.addAtBeginning(
      _buildOutgoingMessage(body: _attachmentLabel(type), type: 'text'),
    );
  }

  String _attachmentLabel(ChatAttachmentType type) {
    if (type.isCamera) {
      return LocaleKeys.camera;
    }
    if (type.isPhotos) {
      return LocaleKeys.chatPhotos;
    }
    if (type.isFile) {
      return LocaleKeys.chatFile;
    }
    return LocaleKeys.chatLocation;
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
      Go.off(
        ChatListScreen(
          conversations: widget.conversation.id is int
              ? ChatContent.conversations
              : null,
        ),
      );
    }
  }

  @override
  Widget build(BuildContext context) {
    return BlocProvider.value(
      value: _chatThreadCubit,
      child: MultiBlocListener(
        listeners: [
          BlocListener<ChatThreadCubit, ChatThreadState>(
            listenWhen: (previous, current) =>
                previous.receivedMessageRevision !=
                current.receivedMessageRevision,
            listener: (context, state) {
              final ChatSocketMessage? message = state.receivedMessage;
              if (message != null) unawaited(_receiveSocketMessage(message));
            },
          ),
          BlocListener<ChatThreadCubit, ChatThreadState>(
            listenWhen: (previous, current) =>
                previous.readReceiptRevision != current.readReceiptRevision,
            listener: (context, state) {
              unawaited(_receiveReadReceipt());
            },
          ),
        ],
        child: _buildScreen(),
      ),
    );
  }

  Widget _buildScreen() {
    return Directionality(
      textDirection: TextDirection.rtl,
      child: Scaffold(
        resizeToAvoidBottomInset: true,
        backgroundColor: AppColors.scaffoldBackground,
        body: SafeArea(
          bottom: false,
          child: Column(
            children: [
              ChatThreadHeader(
                conversation: widget.conversation,
                onReportPressed: _showReportSheet,
              ),
              Expanded(
                child: Column(
                  children: [
                    Container(
                      padding: EdgeInsets.symmetric(
                        horizontal: 9.w,
                        vertical: 3.h,
                      ),
                      decoration: BoxDecoration(
                        color: AppColors.scaffoldBackground,
                        borderRadius: BorderRadius.circular(12.r),
                      ),
                      child: AppText(
                        LocaleKeys.chatToday,
                        color: AppColors.sokoonGray,
                        fontSize: 11.sp,
                      ),
                    ).paddingOnly(top: 10.h, bottom: 2.h),
                    Expanded(
                      child: EasyChat<List<ChatMessageContent>>(
                        controller: _chatController,
                        asyncCall: _loadMessages,
                        mapper: _mapMessages,
                        errorMapper: PagifyErrorMapper(
                          errorWhenDio: (error) {
                            return PagifyApiRequestException(
                              error.message ?? '',
                              pagifyFailure: RequestFailureData(
                                statusCode: error.response?.statusCode,
                                statusMsg: error.response?.statusMessage,
                              ),
                            );
                          },
                        ),
                        messageAlignment: (isFromMe) => isFromMe
                            ? MainAxisAlignment.end
                            : MainAxisAlignment.start,
                        rightMessageBuilder: (message) {
                          return ChatMessageBubble(
                            key: message.message.id is int
                                ? ValueKey<int>(message.message.id as int)
                                : ValueKey<String>(
                                    message.message.id.toString(),
                                  ),
                            message: message,
                            isFromMe: true,
                          );
                        },
                        leftMessageBuilder: (message) {
                          return ChatMessageBubble(
                            key: message.message.id is int
                                ? ValueKey<int>(message.message.id as int)
                                : ValueKey<String>(
                                    message.message.id.toString(),
                                  ),
                            message: message,
                            isFromMe: false,
                          );
                        },
                        loadingBuilder: const Center(
                          child: CircularProgressIndicator(
                            color: AppColors.sokoonTeal,
                          ),
                        ),
                        emptyView: const SizedBox.shrink(),
                        cacheKey: widget.conversation.id is int
                            ? null
                            : ChatData.messagesCacheKey(
                                widget.conversation.id.toString(),
                              ),
                        cacheToJson: _chatMessageToJson,
                        cacheFromJson: _chatMessageFromJson,
                      ).paddingSymmetric(horizontal: 16.w, vertical: 8.h),
                    ),
                    ChatPrivacyBanner(
                      text: LocaleKeys.chatPhonePrivacyThread,
                    ).padding(EdgeInsets.fromLTRB(16.w, 0, 16.w, 10.h)),
                  ],
                ),
              ),
              if (_isRecording)
                ChatVoiceRecordingBar(
                  onCancelPressed: _cancelVoiceRecording,
                  onSendPressed: _sendVoiceMessage,
                )
              else
                ChatComposer(
                  controller: _messageController,
                  onAttachmentPressed: _showAttachments,
                  onVoicePressed: _startVoiceRecording,
                  onSendPressed: _sendTextMessage,
                  showAttachmentAction: widget.conversation.id is int,
                  showVoiceAction: widget.conversation.id is int,
                ),
            ],
          ),
        ),
      ),
    );
  }
}
