import 'dart:async';

import 'package:flutter/material.dart';
import 'package:flutter_bloc/flutter_bloc.dart';
import 'package:melos_core/config/res/config_imports.dart';
import 'package:melos_core/core/helpers/status_builder.dart';
import 'package:melos_core/core/navigation/navigator.dart';

import '../../data/models/chat_content.dart';
import '../cubits/start_chat.dart';
import '../widgets/start_conversation/start_conversation_state_view.dart';
import 'chat_screen.dart';

class StartConversationScreen extends StatefulWidget {
  const StartConversationScreen({super.key, required this.userId});

  final String userId;

  @override
  State<StartConversationScreen> createState() =>
      _StartConversationScreenState();
}

class _StartConversationScreenState extends State<StartConversationScreen> {
  late final CreateConversationCubit _cubit;
  late final Future<void> _createRequest;

  @override
  void initState() {
    super.initState();
    _cubit = CreateConversationCubit();
    _createRequest = _openConversation();
  }

  Future<void> _openConversation() {
    return _cubit.createOrGet(
      userId: widget.userId,
      onSuccess: (conversation) {
        if (!mounted) return;
        Go.off(ChatThreadScreen(conversation: conversation));
      },
    );
  }

  @override
  void dispose() {
    unawaited(_cubit.close());
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: AppColors.scaffoldBackground,
      body: SafeArea(
        child: BlocProvider<CreateConversationCubit>.value(
          value: _cubit,
          child:
              StatusBuilder<
                CreateConversationCubit,
                ConversationContent
              >.withShimmer(
                initialDataForShimmer: const ConversationContent.initial(),
                requestToTryAgainWhenError: _createRequest,
                errorType: ErrorType.customView,
                errorWidget: StartConversationErrorView(
                  onRetryPressed: _openConversation,
                ),
                builder: (_) => const StartConversationLoadingView(),
              ),
        ),
      ),
    );
  }
}
