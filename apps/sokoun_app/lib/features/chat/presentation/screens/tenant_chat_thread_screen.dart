import 'package:flutter/material.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';
import 'package:melos_core/config/language/locale_keys.g.dart';
import 'package:melos_core/config/res/config_imports.dart';
import 'package:melos_core/core/navigation/navigator.dart';
import 'package:melos_core/core/widgets/app_text.dart';
import 'package:melos_core/core/widgets/chat_builder/chat_message.dart';
import 'package:melos_core/core/widgets/chat_builder/easy_chat.dart';
import 'package:pagify/helpers/data_and_pagination_data.dart';
import 'package:pagify/helpers/errors.dart';
import 'package:pagify/pagify.dart';
import 'package:sokoun_app/features/chat/data/enums/tenant_chat_attachment_type.dart';
import 'package:sokoun_app/features/chat/data/models/tenant_chat_content.dart';

import '../widgets/imports.dart';
import 'tenant_chat_list_screen.dart';

class TenantChatThreadScreen extends StatefulWidget {
  const TenantChatThreadScreen({super.key, required this.conversation});

  final TenantConversationContent conversation;

  @override
  State<TenantChatThreadScreen> createState() => _TenantChatThreadScreenState();
}

class _TenantChatThreadScreenState extends State<TenantChatThreadScreen> {
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

  Future<List<TenantChatMessageContent>> _loadMessages(
    BuildContext context,
    int currentPage,
  ) async {
    if (currentPage > 1) {
      return const [];
    }
    return TenantChatContent.initialMessages;
  }

  PagifyData<ChatMessages> _mapMessages(
    List<TenantChatMessageContent> response,
  ) {
    return PagifyData(
      data: response.reversed.map(_toChatMessage).toList(growable: false),
      paginationData: PaginationData(perPage: 20, totalPages: 1),
    );
  }

  ChatMessages _toChatMessage(TenantChatMessageContent content) {
    return ChatMessages(
      message: Message(id: content.id, type: content.type, body: content.body),
      sender: Sender(
        id: content.isFromMe ? 'tenant' : '${widget.conversation.id}',
        name: content.isFromMe ? 'tenant' : widget.conversation.name,
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
      sender: Sender(id: 'tenant', name: 'tenant', image: '', isFromMe: true),
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
        return TenantChatAttachmentsSheet(
          onAttachmentSelected: _selectAttachment,
        );
      },
    );
  }

  void _selectAttachment(TenantChatAttachmentType type) {
    Go.back();
    _chatController.addAtBeginning(
      _buildOutgoingMessage(body: _attachmentLabel(type), type: 'text'),
    );
  }

  String _attachmentLabel(TenantChatAttachmentType type) {
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
      builder: (context) {
        return TenantChatReportSheet(
          onSubmitted: (selectedReason, details) => Go.back(true),
        );
      },
    );

    if (submitted == true && mounted) {
      Go.off(const TenantChatListScreen());
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
              TenantChatThreadHeader(
                conversation: widget.conversation,
                onBackPressed: () => Go.back(),
                onReportPressed: _showReportSheet,
              ),
              Expanded(
                child: Column(
                  children: [
                    Padding(
                      padding: EdgeInsets.only(top: 10.h, bottom: 2.h),
                      child: Container(
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
                      ),
                    ),
                    Expanded(
                      child: Padding(
                        padding: EdgeInsets.symmetric(
                          horizontal: 16.w,
                          vertical: 8.h,
                        ),
                        child: EasyChat<List<TenantChatMessageContent>>(
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
                            return TenantChatMessageBubble(
                              message: message,
                              isFromMe: true,
                            );
                          },
                          leftMessageBuilder: (message) {
                            return TenantChatMessageBubble(
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
                        ),
                      ),
                    ),
                    Padding(
                      padding: EdgeInsets.fromLTRB(16.w, 0, 16.w, 10.h),
                      child: ChatPrivacyBanner(
                        text: LocaleKeys.chatPhonePrivacyThread,
                      ),
                    ),
                  ],
                ),
              ),
              if (_isRecording)
                TenantChatVoiceRecordingBar(
                  onCancelPressed: _cancelVoiceRecording,
                  onSendPressed: _sendVoiceMessage,
                )
              else
                TenantChatComposer(
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
