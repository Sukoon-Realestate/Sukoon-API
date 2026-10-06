import 'package:flutter/material.dart';
import 'package:melos_core/config/language/locale_keys.g.dart';
import 'package:melos_core/config/res/config_imports.dart';

import '../../../data/models/chat_content.dart';
import 'chat_report_sheet.dart';

class ChatReportButton extends StatelessWidget {
  const ChatReportButton({super.key, required this.conversation});
  final ConversationContent conversation;

  Future<void> _showReportSheet(BuildContext context) async {
    await showModalBottomSheet<bool>(
      context: context,
      isScrollControlled: true,
      useSafeArea: true,
      backgroundColor: AppColors.transparent,
      barrierColor: AppColors.blackAlpha50,
      builder: (_) => ChatReportSheet(conversation: conversation),
    );
  }

  @override
  Widget build(BuildContext context) => IconButton(
    tooltip: LocaleKeys.chatReportProblemTitle,
    onPressed: conversation.id.isEmpty ? null : () => _showReportSheet(context),
    icon: const Icon(Icons.more_vert_rounded),
  );
}
