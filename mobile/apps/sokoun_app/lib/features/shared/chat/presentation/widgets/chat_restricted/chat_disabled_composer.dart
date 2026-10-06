import 'package:melos_core/config/language/locale_keys.g.dart';
import 'package:flutter/material.dart';

import '../chat_unavailable_indicator.dart';

class ChatDisabledComposer extends StatelessWidget {
  const ChatDisabledComposer({super.key});

  @override
  Widget build(BuildContext context) {
    return ChatUnavailableIndicator(
      message: LocaleKeys.chatTypingDisabled,
      icon: Icons.lock_outline_rounded,
    );
  }
}
