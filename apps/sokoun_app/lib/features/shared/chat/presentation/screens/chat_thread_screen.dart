import 'package:flutter/material.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';
import 'package:melos_core/config/language/locale_keys.g.dart';
import 'package:melos_core/config/res/config_imports.dart';
import 'package:melos_core/core/extensions/padding_extension.dart';
import 'package:melos_core/core/navigation/navigator.dart';
import 'package:melos_core/core/widgets/app_text.dart';
import 'package:melos_core/core/widgets/chat_builder/chat_message.dart';
import 'package:melos_core/core/widgets/chat_builder/easy_chat.dart';
import 'package:pagify/helpers/data_and_pagination_data.dart';
import 'package:pagify/helpers/errors.dart';
import 'package:pagify/pagify.dart';
import 'package:sokoun_app/features/shared/chat/data/enums/chat_attachment_type.dart';
import 'package:sokoun_app/features/shared/chat/data/models/chat_content.dart';

import '../widgets/imports.dart';
import 'chat_list_screen.dart';

class ChatThreadScreen extends StatefulWidget {
  const ChatThreadScreen({super.key, required this.conversation});

  final ConversationContent conversation;

  @override
  State<ChatThreadScreen> createState() => _ChatThreadScreenState();
}

class _ChatThreadScreenState extends State<ChatThreadScreen> {
  late final PagifyController<ChatMessages> _chatController;
  late final TextEditingController _messageController;
  int _nextMessageId = 100;
  bool _isRecording = false;

  @override
  void initState() {
    super.initState();
    _chatController = PagifyController<ChatMessages>();
    _messageController = TextEditingController();
  }

  @override
  void dispose() {
    _chatController.dispose();
    _messageController.dispose();
    super.dispose();
  }

  Future<List<ChatMessageContent>> _loadMessages(
    BuildContext context,
    int currentPage,
  ) async {
    if (currentPage > 1) {
      return const [];
    }
    return ChatContent.initialMessages;
  }

  PagifyData<ChatMessages> _mapMessages(List<ChatMessageContent> response) {
    return PagifyData(
      data: response.reversed.map(_toChatMessage).toList(growable: false),
      paginationData: PaginationData(perPage: 20, totalPages: 1),
    );
  }

  ChatMessages _toChatMessage(ChatMessageContent content) {
    return ChatMessages(
      message: Message(id: content.id, type: content.type, body: content.body),
      sender: Sender(
        id: content.isFromMe ? 'current-user' : '${widget.conversation.id}',
        name: content.isFromMe ? 'current-user' : widget.conversation.name,
        image: '',
        isFromMe: content.isFromMe,
      ),
      time: content.time,
      messageState: MessageState.read,
    );
  }

  void _sendTextMessage() {
    final String text = _messageController.text.trim();
    if (text.isEmpty) {
      return;
    }

    _chatController.addAtBeginning(
      _buildOutgoingMessage(body: text, type: 'text'),
    );
    _messageController.clear();
    FocusScope.of(context).unfocus();
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
      messageState: MessageState.sent,
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
      Go.off(const ChatListScreen());
    }
  }

  @override
  Widget build(BuildContext context) {
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
                            message: message,
                            isFromMe: true,
                          );
                        },
                        leftMessageBuilder: (message) {
                          return ChatMessageBubble(
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
                ),
            ],
          ),
        ),
      ),
    );
  }
}
