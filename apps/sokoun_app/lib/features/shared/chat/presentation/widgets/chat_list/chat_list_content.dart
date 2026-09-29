import 'dart:async';

import 'package:flutter/material.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';
import 'package:melos_core/config/language/locale_keys.g.dart';
import 'package:melos_core/config/res/config_imports.dart';
import 'package:melos_core/core/extensions/padding_extension.dart';
import 'package:melos_core/core/helpers/text_style_manager.dart';
import 'package:melos_core/core/navigation/navigator.dart';
import 'package:melos_core/core/widgets/app_pagify.dart';
import 'package:melos_core/core/widgets/app_text.dart';
import 'package:pagify/pagify.dart';

import '../../../data/chats_data.dart';
import '../../../data/chat_realtime_service.dart';
import '../../../data/chat_unread_refresh_bus.dart';
import '../../../data/models/chat_content.dart';
import '../../../data/models/chat_socket_message.dart';
import '../../screens/chat_search_screen.dart';
import '../shared/chat_privacy_banner.dart';
import 'chat_empty_state.dart';
import '../chat_list_tile.dart';
import 'chat_search_field.dart';

class ChatListContent extends StatefulWidget {
  const ChatListContent({super.key});

  @override
  State<ChatListContent> createState() => _ChatListContentState();
}

class _ChatListContentState extends State<ChatListContent> {
  late final ChatDataSource _dataSource;
  late final PagifyController<ConversationContent> _pagifyController;
  StreamSubscription<ChatSocketMessage>? _messageSubscription;
  StreamSubscription<int>? _unreadRefreshSubscription;

  @override
  void initState() {
    super.initState();
    _dataSource = ChatData.source;
    _pagifyController = PagifyController<ConversationContent>();
    _messageSubscription = ChatRealtimeService.instance.messages.listen(
      (_) => unawaited(_pagifyController.refresh()),
    );
    _unreadRefreshSubscription = ChatUnreadRefreshBus.stream.listen((removed) {
      if (removed == 0) unawaited(_pagifyController.refresh());
    });
  }

  @override
  void dispose() {
    unawaited(_messageSubscription?.cancel());
    unawaited(_unreadRefreshSubscription?.cancel());
    super.dispose();
  }

  void _openSearch() {
    Go.to(ChatSearchScreen(conversations: _pagifyController.items));
  }

  @override
  Widget build(BuildContext context) {
    final String? cacheKey = _dataSource.conversationsCacheKey;
    return Column(
      crossAxisAlignment: CrossAxisAlignment.stretch,
      children: [
        AppText(
          LocaleKeys.chatConversationsTitle,
          style: AppTextStyles.bold.copyWith(
            color: AppColors.sokoonNavy,
            fontSize: 20.sp,
          ),
        ).padding(EdgeInsets.fromLTRB(20.w, 4.h, 20.w, 12.h)),
        ChatSearchField(
          readOnly: true,
          onTap: _openSearch,
        ).paddingSymmetric(horizontal: 20.w),
        ChatPrivacyBanner(
          text: LocaleKeys.chatPhonePrivacyInbox,
        ).padding(EdgeInsets.fromLTRB(8.w, 12.h, 8.w, 0)),
        Expanded(
          child: AppPagify<ConversationContent>(
            pagifyController: _pagifyController,
            asyncCall: (_, page) =>
                _dataSource.getConversationsPage(page: page),
            shrinkWrap: false,
            cacheKey: cacheKey,
            cacheToJson: cacheKey == null
                ? null
                : (conversation) => conversation.toJson(),
            cacheFromJson: cacheKey == null
                ? null
                : ConversationContent.fromJson,
            emptyListView: const ChatEmptyState(),
            itemBuilder: (context, data, index, conversation) => Column(
              mainAxisSize: MainAxisSize.min,
              children: [
                ChatListTile(
                  key: ValueKey<String>(conversation.id),
                  conversation: conversation,
                ),
                Divider(
                  height: 1.h,
                  thickness: 1.h,
                  color: AppColors.sokoonBorder,
                ),
              ],
            ),
          ),
        ),
      ],
    );
  }
}
