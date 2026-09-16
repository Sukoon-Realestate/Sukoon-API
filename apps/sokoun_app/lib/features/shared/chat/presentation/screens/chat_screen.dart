import 'dart:async';

import 'package:flutter/material.dart';
import 'package:flutter_bloc/flutter_bloc.dart';
import 'package:melos_core/config/res/config_imports.dart';

import '../../data/chat_unread_refresh_bus.dart';
import '../../data/models/chat_content.dart';
import '../cubits/socket_cubit.dart';
import '../widgets/chat_thread/chat_thread_content.dart';

class ChatScreen extends StatefulWidget {
  const ChatScreen({super.key, required this.conversation});

  final ConversationContent conversation;

  @override
  State<ChatScreen> createState() => _ChatScreenState();
}

class _ChatScreenState extends State<ChatScreen> with WidgetsBindingObserver {
  late final SocketCubit _chatThreadCubit;

  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addObserver(this);
    _chatThreadCubit = SocketCubit(
      conversationId: widget.conversation.id,
      otherParticipantId: widget.conversation.otherParticipant.id,
    );
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

/// Backwards-compatible name used by existing navigation call sites.
class ChatThreadScreen extends ChatScreen {
  const ChatThreadScreen({super.key, required super.conversation});
}
