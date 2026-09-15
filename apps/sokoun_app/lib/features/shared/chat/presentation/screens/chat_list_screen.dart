import 'dart:async';

import 'package:flutter/material.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';
import 'package:melos_core/config/language/locale_keys.g.dart';
import 'package:melos_core/config/res/config_imports.dart';
import 'package:melos_core/core/extensions/padding_extension.dart';
import 'package:melos_core/core/navigation/navigator.dart';
import 'package:melos_core/core/widgets/app_text.dart';
import 'package:melos_core/core/widgets/app_pagify.dart';
import 'package:pagify/pagify.dart';
import 'package:sokoun_app/features/shared/chat/data/chat_data.dart';
import 'package:sokoun_app/features/shared/chat/data/chat_realtime_service.dart';
import 'package:sokoun_app/features/shared/chat/data/chat_unread_refresh_bus.dart';
import 'package:sokoun_app/features/shared/chat/data/models/chat_content.dart';
import 'package:sokoun_app/features/shared/chat/data/models/chat_socket_message.dart';

import '../widgets/imports.dart';
import 'chat_empty_screen.dart';
import 'chat_search_screen.dart';

class ChatListScreen extends StatefulWidget {
  const ChatListScreen({super.key, this.conversations});

  /// A non-null value is a fixture source used by previews and widget tests.
  /// Production callers pass null so the documented REST endpoint is used.
  final List<ConversationContent>? conversations;

  @override
  State<ChatListScreen> createState() => _ChatListScreenState();
}

class _ChatListScreenState extends State<ChatListScreen> {
  late final PagifyController<ConversationContent> _pagifyController;
  late final bool _usesApi;
  StreamSubscription<ChatSocketMessage>? _messageSubscription;
  StreamSubscription<int>? _unreadRefreshSubscription;

  @override
  void initState() {
    super.initState();
    _pagifyController = PagifyController<ConversationContent>();
    _usesApi = widget.conversations == null;
    if (_usesApi) {
      _messageSubscription = ChatRealtimeService.instance.messages.listen(
        (_) => unawaited(_pagifyController.refresh()),
      );
      _unreadRefreshSubscription = ChatUnreadRefreshBus.stream.listen((
        removed,
      ) {
        if (removed == 0) unawaited(_pagifyController.refresh());
      });
    }
  }

  @override
  void dispose() {
    unawaited(_messageSubscription?.cancel());
    unawaited(_unreadRefreshSubscription?.cancel());
    super.dispose();
  }

  void _openSearch() {
    final List<ConversationContent> conversations =
        _fixtureConversations ?? _pagifyController.items;
    Go.to(
      ChatSearchScreen(
        conversations: conversations,
        includeFixtureProperties: !_usesApi,
      ),
    );
  }

  List<ConversationContent>? get _fixtureConversations {
    return widget.conversations;
  }

  @override
  Widget build(BuildContext context) {
    final List<ConversationContent>? fixtures = _fixtureConversations;
    if (fixtures != null && fixtures.isEmpty) {
      return const ChatEmptyScreen();
    }

    return Directionality(
      textDirection: TextDirection.rtl,
      child: Scaffold(
        backgroundColor: AppColors.scaffoldBackground,
        body: SafeArea(
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: [
              AppText(
                LocaleKeys.chatConversationsTitle,
                color: AppColors.sokoonNavy,
                fontSize: 20.sp,
                fontWeight: FontWeight.w900,
              ).padding(EdgeInsets.fromLTRB(20.w, 4.h, 20.w, 12.h)),
              ChatSearchField(
                readOnly: true,
                onTap: _openSearch,
              ).paddingSymmetric(horizontal: 20.w),
              ChatPrivacyBanner(
                text: LocaleKeys.chatPhonePrivacyInbox,
              ).padding(EdgeInsets.fromLTRB(8.w, 12.h, 8.w, 0)),
              Expanded(
                child: fixtures == null
                    ? AppPagify<ConversationContent>(
                        pagifyController: _pagifyController,
                        asyncCall: (_, page) =>
                            ChatData.getConversationsPage(page: page),
                        shrinkWrap: false,
                        cacheKey: ChatData.conversationsCacheKey,
                        cacheToJson: (conversation) => conversation.toJson(),
                        cacheFromJson: ConversationContent.fromJson,
                        emptyListView: const ChatEmptyState(),
                        itemBuilder: (context, data, index, conversation) =>
                            _ConversationListRow(conversation: conversation),
                      )
                    : ListView.builder(
                        padding: EdgeInsets.only(top: 10.h, bottom: 14.h),
                        itemCount: fixtures.length,
                        itemBuilder: (context, index) =>
                            _ConversationListRow(conversation: fixtures[index]),
                      ),
              ),
            ],
          ),
        ),
      ),
    );
  }
}

class _ConversationListRow extends StatelessWidget {
  const _ConversationListRow({required this.conversation});

  final ConversationContent conversation;

  @override
  Widget build(BuildContext context) {
    return Column(
      mainAxisSize: MainAxisSize.min,
      children: [
        ChatListItem(
          key: conversation.id is int
              ? ValueKey<int>(conversation.id as int)
              : ValueKey<String>(conversation.id.toString()),
          conversation: conversation,
        ),
        Divider(height: 1.h, thickness: 1.h, color: AppColors.sokoonBorder),
      ],
    );
  }
}
