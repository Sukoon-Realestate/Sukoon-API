import 'package:flutter/material.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';
import 'package:melos_core/config/language/locale_keys.g.dart';
import 'package:melos_core/config/res/config_imports.dart';
import 'package:melos_core/core/extensions/padding_extension.dart';
import 'package:melos_core/core/shared/models/user_models/user_model.dart';
import 'package:melos_core/core/widgets/chat_builder/chat_message.dart';
import 'package:melos_core/core/widgets/chat_builder/easy_chat.dart';
import 'package:pagify/helpers/data_and_pagination_data.dart';
import 'package:pagify/helpers/errors.dart';
import 'package:pagify/pagify.dart';

import '../../../data/chat_data.dart';
import '../../../data/models/chat_content.dart';
import '../shared/chat_privacy_banner.dart';
import 'chat_day_label.dart';
import 'chat_message_bubble.dart';
import 'chat_messages_empty_state.dart';

class ChatThreadMessagesView extends StatefulWidget {
  const ChatThreadMessagesView({
    super.key,
    required this.conversation,
    required this.controller,
  });

  final ConversationContent conversation;
  final PagifyController<ChatMessages> controller;

  @override
  State<ChatThreadMessagesView> createState() => _ChatThreadMessagesViewState();
}

class _ChatThreadMessagesViewState extends State<ChatThreadMessagesView> {
  late final ChatDataSource _dataSource;
  PaginationData _pagination = PaginationData(
    perPage: ChatData.messagesPageSize,
    totalPages: 1,
  );

  @override
  void initState() {
    super.initState();
    _dataSource = ChatData.source;
  }

  Future<List<ChatMessageContent>> _loadMessages(
    BuildContext context,
    int currentPage,
  ) async {
    final (List<ChatMessageContent>, PaginationData) page = await _dataSource
        .getMessagesPage(
          conversationId: widget.conversation.id,
          page: currentPage,
        );
    _pagination = page.$2;
    return page.$1;
  }

  PagifyData<ChatMessages> _mapMessages(List<ChatMessageContent> response) {
    return PagifyData(
      data: response.reversed.map(_toChatMessage).toList(growable: false),
      paginationData: _pagination,
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
            : widget.conversation.id,
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

  Map<String, dynamic> _messageToJson(ChatMessages item) => {
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

  ChatMessages _messageFromJson(Map<String, dynamic> json) {
    final String stateName = json['message_state']?.toString() ?? '';
    return ChatMessages(
      message: Message(
        id: json['id']?.toString() ?? '',
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

  @override
  Widget build(BuildContext context) {
    final String? cacheKey = _dataSource.messagesCacheKey(
      widget.conversation.id,
    );
    return Column(
      children: [
        const ChatDayLabel(),
        Expanded(
          child: EasyChat<List<ChatMessageContent>>(
            controller: widget.controller,
            asyncCall: _loadMessages,
            mapper: _mapMessages,
            errorMapper: PagifyErrorMapper(
              errorWhenDio: (error) => PagifyApiRequestException(
                error.message ?? '',
                pagifyFailure: RequestFailureData(
                  statusCode: error.response?.statusCode,
                  statusMsg: error.response?.statusMessage,
                ),
              ),
            ),
            messageAlignment: (isFromMe) =>
                isFromMe ? MainAxisAlignment.end : MainAxisAlignment.start,
            rightMessageBuilder: (message) => ChatMessageBubble(
              key: ValueKey<String>(message.message.id.toString()),
              message: message,
              isFromMe: true,
            ),
            leftMessageBuilder: (message) => ChatMessageBubble(
              key: ValueKey<String>(message.message.id.toString()),
              message: message,
              isFromMe: false,
            ),
            loadingBuilder: const Center(
              child: CircularProgressIndicator(color: AppColors.sokoonTeal),
            ),
            emptyView: const ChatMessagesEmptyState(),
            cacheKey: cacheKey,
            cacheToJson: cacheKey == null ? null : _messageToJson,
            cacheFromJson: cacheKey == null ? null : _messageFromJson,
          ).paddingSymmetric(horizontal: 16.w, vertical: 8.h),
        ),
        ChatPrivacyBanner(
          text: LocaleKeys.chatPhonePrivacyThread,
        ).padding(EdgeInsets.fromLTRB(16.w, 0, 16.w, 10.h)),
      ],
    );
  }
}
