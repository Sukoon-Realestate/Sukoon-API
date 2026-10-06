import 'package:flutter/material.dart';
import 'package:flutter_bloc/flutter_bloc.dart';
import 'package:melos_core/config/language/locale_keys.g.dart';
import 'package:melos_core/core/widgets/app_text.dart';
import 'package:melos_core/core/widgets/toast_messages/toast_message.dart';
import '../../../data/models/chat_local_state.dart';
import '../../cubits/chat_thread_cubit.dart';

class ChatRecoveredMessages extends StatelessWidget {
  const ChatRecoveredMessages({super.key});
  @override
  Widget build(BuildContext context) =>
      BlocSelector<ChatThreadCubit, ChatThreadState, List<SavedChatMessage>>(
        selector: (state) => state.recoveredMessages,
        builder: (context, messages) => messages.isEmpty
            ? const SizedBox.shrink()
            : ConstrainedBox(
                constraints: const BoxConstraints(maxHeight: 180),
                child: SingleChildScrollView(
                  child: Column(
                    children: [
                      AppText(
                        LocaleKeys.freeRecoveredChat,
                        textAlign: TextAlign.center,
                      ),
                      for (final message in messages)
                        ListTile(
                          key: ValueKey(message.id),
                          title: AppText(
                            message.content,
                            maxLines: 2,
                            overflow: TextOverflow.ellipsis,
                          ),
                          trailing: TextButton(
                            onPressed: () async {
                              try {
                                if (!await context
                                    .read<ChatThreadCubit>()
                                    .restoreMessageDraft(message)) {
                                  Messages.showToast(
                                    msg: LocaleKeys.freeChatDraftExists,
                                  );
                                }
                              } catch (_) {
                                Messages.showToast(
                                  msg: LocaleKeys.freeLocalSaveFailed,
                                );
                              }
                            },
                            child: AppText(LocaleKeys.freeRestoreMessage),
                          ),
                        ),
                    ],
                  ),
                ),
              ),
      );
}
