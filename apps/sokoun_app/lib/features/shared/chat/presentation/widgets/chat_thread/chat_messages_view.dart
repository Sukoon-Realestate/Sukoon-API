import 'package:flutter_bloc/flutter_bloc.dart';
import '../../cubits/chat_thread_cubit.dart';
import 'package:flutter/material.dart';
import 'package:sokoun_app/features/shared/contact/presentation/widgets/revealed_phone_card.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';
import 'package:melos_core/config/language/locale_keys.g.dart';
import 'package:melos_core/core/extensions/padding_extension.dart';
import 'package:melos_core/core/shared/models/user_models/user_model.dart';
import 'package:melos_core/core/widgets/chat_builder/chat_message.dart';
import 'package:melos_core/core/widgets/chat_builder/easy_chat.dart';
import 'package:melos_core/core/widgets/custom_loading.dart';
import 'package:pagify/helpers/data_and_pagination_data.dart';
import 'package:pagify/helpers/errors.dart';
import 'package:pagify/pagify.dart';

import '../../../data/chat_data.dart';
import '../../../data/models/chat_content.dart';
import '../shared/chat_privacy_banner.dart';
import 'chat_day_label.dart';
import 'chat_messages_empty_state.dart';
import 'chat_message_bubble.dart';

class ChatMessagesView extends StatefulWidget {
  const ChatMessagesView({
    super.key,
    required this.conversation,
    required this.controller,
    required this.initialMessagesRequest,
    required this.messagesCacheKey,
  });

  final ConversationContent conversation;
  final PagifyController<ChatMessages> controller;
  final Future<List<ChatMessageContent>> initialMessagesRequest;
  final String? messagesCacheKey;

  @override
  State<ChatMessagesView> createState() => _ChatMessagesViewState();
}

class _ChatMessagesViewState extends State<ChatMessagesView> {
  PaginationData _pagination = PaginationData(
    perPage: ChatData.messagesPageSize,
    totalPages: 1,
  );

  Future<List<ChatMessageContent>> _loadMessages(BuildContext _, int _) async {
    final List<ChatMessageContent> messages =
        await widget.initialMessagesRequest;
    if (mounted) {
      await context.read<ChatThreadCubit>().reconcileHistory(messages);
    }
    _pagination = PaginationData(
      perPage: ChatData.messagesPageSize,
      totalPages: 1,
    );
    return messages;
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
      createdAt: createdAt,
      messageState: MessageState.read,
    );
  }

  @override
  Widget build(BuildContext context) {
    return LayoutBuilder(
      builder: (context, constraints) => Column(
        children: [
          Expanded(
            child: EasyChat<List<ChatMessageContent>>(
              controller: widget.controller,
              itemHeaderBuilder: _dayHeader,
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
              messageAlignment: (isFromMe) => _messageAlignment(isFromMe),
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
              loadingBuilder: CustomLoading.showLoadingView(),
              emptyView: const ChatMessagesEmptyState(),
            ).paddingSymmetric(horizontal: 16.w, vertical: 8.h),
          ),
          ConstrainedBox(
            constraints: BoxConstraints(maxHeight: constraints.maxHeight * .3),
            child: NotificationListener<ScrollNotification>(
              // Footer scrolling must not change the conversation's reading
              // position or make incoming messages jump to the latest item.
              onNotification: (_) => true,
              child: SingleChildScrollView(
                child:
                    (widget
                                .conversation
                                .otherParticipant
                                .revealedPhone
                                .isNotEmpty
                            ? RevealedPhoneCard(
                                phoneNumber: widget
                                    .conversation
                                    .otherParticipant
                                    .revealedPhone,
                              )
                            : ChatPrivacyBanner(
                                icon:
                                    widget
                                        .conversation
                                        .otherParticipant
                                        .isPhoneRevealed
                                    ? Icons.info_outline_rounded
                                    : Icons.lock_outline_rounded,
                                text:
                                    widget
                                        .conversation
                                        .otherParticipant
                                        .isPhoneRevealed
                                    ? LocaleKeys.contactPhoneUnavailable
                                    : LocaleKeys.chatPhonePrivacyThread,
                              ))
                        .padding(EdgeInsets.fromLTRB(16.w, 0, 16.w, 10.h)),
              ),
            ),
          ),
        ],
      ),
    );
  }

  Widget? _dayHeader(List<ChatMessages> messages, int index) {
    final DateTime? date = messages[index].createdAt;
    if (date == null) return null;
    final DateTime? previous = index > 0 ? messages[index - 1].createdAt : null;
    if (previous != null && DateUtils.isSameDay(date, previous)) return null;
    return Center(child: ChatDayLabel(date: date));
  }

  MainAxisAlignment _messageAlignment(bool isFromMe) {
    final bool isRtl = Directionality.of(context) == TextDirection.rtl;
    if (isRtl) {
      return isFromMe ? MainAxisAlignment.start : MainAxisAlignment.end;
    }
    return isFromMe ? MainAxisAlignment.end : MainAxisAlignment.start;
  }
}
