import 'dart:async';

import 'package:flutter/material.dart';
import 'package:flutter_bloc/flutter_bloc.dart';
import 'package:melos_core/config/res/config_imports.dart';

import '../../data/chat_unread_refresh_bus.dart';
import '../../data/models/chat_content.dart';
import '../cubits/chat_thread_cubit.dart';
import '../widgets/chat_thread/chat_thread_content.dart';

class ChatThreadScreen extends StatefulWidget {
  const ChatThreadScreen({super.key, required this.conversation});

  final ConversationContent conversation;

  @override
  State<ChatThreadScreen> createState() => _ChatThreadScreenState();
}

class _ChatThreadScreenState extends State<ChatThreadScreen>
    with WidgetsBindingObserver {
  late final ChatThreadCubit _chatThreadCubit;

  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addObserver(this);
    _chatThreadCubit = ChatThreadCubit(conversationId: widget.conversation.id);
    ChatUnreadRefreshBus.requestRefresh(
      removedUnreadCount: widget.conversation.unreadCount,
    );
    unawaited(_chatThreadCubit.connect());
  }

  @override
  void didChangeAppLifecycleState(AppLifecycleState state) {
    unawaited(_chatThreadCubit.onAppLifecycleStateChanged(state));
  }

  @override
  void dispose() {
    WidgetsBinding.instance.removeObserver(this);
    unawaited(_chatThreadCubit.close());
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return BlocProvider<ChatThreadCubit>.value(
      value: _chatThreadCubit,
      child: Scaffold(
        resizeToAvoidBottomInset: true,
        backgroundColor: AppColors.scaffoldBackground,
        body: SafeArea(
          bottom: false,
          child: ChatThreadContent(conversation: widget.conversation),
        ),
      ),
    );
  }
}
