import 'dart:async';

import 'package:flutter/material.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';
import 'package:melos_core/config/language/locale_keys.g.dart';
import 'package:melos_core/config/res/config_imports.dart';
import 'package:melos_core/core/extensions/padding_extension.dart';
import 'package:melos_core/core/navigation/navigator.dart';
import 'package:melos_core/core/network/account_session.dart';
import 'package:melos_core/core/shared/route_observer.dart';
import 'package:melos_core/core/widgets/app_pagify.dart';
import 'package:pagify/pagify.dart';

import '../../../data/chat_data.dart';
import '../../../data/chat_unread_refresh_bus.dart';
import '../../../data/models/chat_content.dart';
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

class _ChatListContentState extends State<ChatListContent> with RouteAware {
  late final ChatDataSource _dataSource;
  late final PagifyController<ConversationContent> _pagifyController;
  final int _sessionGeneration = AccountSession.generation;
  ModalRoute<dynamic>? _route;
  bool _needsRefresh = false;
  StreamSubscription<int>? _unreadRefreshSubscription;

  @override
  void initState() {
    super.initState();
    _dataSource = ChatData.source;
    _pagifyController = PagifyController<ConversationContent>();
    _unreadRefreshSubscription = ChatUnreadRefreshBus.stream.listen((_) {
      if (_sessionGeneration == AccountSession.generation &&
          _route?.isCurrent == false) {
        _needsRefresh = true;
      }
    });
  }

  @override
  void didChangeDependencies() {
    super.didChangeDependencies();
    final route = ModalRoute.of(context);
    if (identical(_route, route)) return;
    AppNavigationObserver.instance.unsubscribe(this);
    _route = route;
    if (route != null) AppNavigationObserver.instance.subscribe(this, route);
  }

  @override
  void didPopNext() {
    // Wait for the navigator to restore the list's route and tab visibility.
    WidgetsBinding.instance.addPostFrameCallback((_) {
      if (!mounted ||
          !_needsRefresh ||
          _sessionGeneration != AccountSession.generation ||
          _route?.isCurrent != true) {
        return;
      }
      _needsRefresh = false;
      if (!TickerMode.of(context)) return;
      _pagifyController.refresh();
    });
  }

  @override
  void dispose() {
    AppNavigationObserver.instance.unsubscribe(this);
    _unreadRefreshSubscription?.cancel();
    super.dispose();
  }

  void _openSearch() {
    Go.to(ChatSearchScreen(conversations: _pagifyController.items));
  }

  @override
  Widget build(BuildContext context) {
    final String? cacheKey = _dataSource.conversationsCacheKey;
    return AppPagify<ConversationContent>(
      enablePullRefresh: true,
      pagifyController: _pagifyController,
      asyncCall: (_, page) => _dataSource.getConversationsPage(page: page),
      shrinkWrap: false,
      cacheKey: cacheKey,
      cacheToJson: cacheKey == null
          ? null
          : (conversation) => conversation.toJson(),
      cacheFromJson: cacheKey == null ? null : ConversationContent.fromJson,
      emptyListView: const ChatEmptyState(),
      header: Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          ChatSearchField(
            readOnly: true,
            onTap: _openSearch,
          ).paddingSymmetric(horizontal: 20.w),
          ChatPrivacyBanner(
            text: LocaleKeys.chatPhonePrivacyInbox,
          ).padding(EdgeInsets.fromLTRB(8.w, 12.h, 8.w, 0)),
        ],
      ),
      itemBuilder: (context, data, index, conversation) => Column(
        mainAxisSize: MainAxisSize.min,
        children: [
          ChatListTile(
            key: ValueKey<String>(conversation.id),
            conversation: conversation,
          ),
          Divider(height: 1.h, thickness: 1.h, color: AppColors.sokoonBorder),
        ],
      ),
    );
  }
}
