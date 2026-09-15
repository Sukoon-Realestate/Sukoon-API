import 'dart:async';

import 'package:flutter/material.dart';
import 'package:flutter_bloc/flutter_bloc.dart';
import 'package:melos_core/config/language/locale_keys.g.dart';
import 'package:melos_core/config/res/config_imports.dart';
import 'package:melos_core/core/base_crud/code/presentation/cubit/base_cubit/async_cubit.dart';
import 'package:melos_core/core/navigation/navigator.dart';
import 'package:melos_core/core/widgets/app_text.dart';

import '../../data/models/chat_content.dart';
import '../cubits/create_conversation_cubit.dart';
import 'chat_thread_screen.dart';

class StartConversationScreen extends StatefulWidget {
  const StartConversationScreen({super.key, required this.userId});

  final String userId;

  @override
  State<StartConversationScreen> createState() =>
      _StartConversationScreenState();
}

class _StartConversationScreenState extends State<StartConversationScreen> {
  late final CreateConversationCubit _cubit;

  @override
  void initState() {
    super.initState();
    _cubit = CreateConversationCubit();
    unawaited(_openConversation());
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
    return Directionality(
      textDirection: TextDirection.rtl,
      child: Scaffold(
        backgroundColor: AppColors.scaffoldBackground,
        body: SafeArea(
          child: BlocProvider<CreateConversationCubit>.value(
            value: _cubit,
            child:
                BlocBuilder<
                  CreateConversationCubit,
                  AsyncState<ConversationContent>
                >(
                  builder: (context, state) {
                    if (state.isError) {
                      return Center(
                        child: TextButton.icon(
                          onPressed: _openConversation,
                          icon: const Icon(
                            Icons.refresh_rounded,
                            color: AppColors.sokoonTeal,
                          ),
                          label: AppText(
                            LocaleKeys.operationFaild,
                            color: AppColors.sokoonNavy,
                          ),
                        ),
                      );
                    }
                    return const Center(
                      child: CircularProgressIndicator(
                        color: AppColors.sokoonTeal,
                      ),
                    );
                  },
                ),
          ),
        ),
      ),
    );
  }
}
