import 'package:melos_core/config/language/locale_keys.g.dart';
import 'package:sokoun_app/shared_widgets/app_scaffold.dart';

import 'package:flutter/material.dart';
import 'package:flutter_bloc/flutter_bloc.dart';
import 'package:melos_core/config/res/config_imports.dart';
import 'package:melos_core/core/navigation/navigator.dart';

import '../../data/models/chat_content.dart';
import '../cubits/create_conversation_cubit.dart';
import '../widgets/chat_status_builder.dart';
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
        Go.off(ChatScreen(conversation: conversation));
      },
    );
  }

  @override
  void dispose() {
    _cubit.close();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return AppScaffold(
      title: LocaleKeys.chatConversationsTitle,
      showBackButton: true,
      backgroundColor: context.appColor(
        AppColors.scaffoldBackground,
        surface: true,
      ),
      body: SafeArea(
        child: BlocProvider<CreateConversationCubit>.value(
          value: _cubit,
          child:
              ChatStatusBuilder<CreateConversationCubit, ConversationContent>(
                initialData: const ConversationContent.initial(),
                request: _createRequest,
                onRetry: _openConversation,
                builder: (_) => const StartConversationLoadingView(),
              ),
        ),
      ),
    );
  }
}
