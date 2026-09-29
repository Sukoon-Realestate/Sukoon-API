import 'package:flutter/material.dart';
import 'package:melos_core/config/language/locale_keys.g.dart';
import 'package:melos_core/config/res/config_imports.dart';
import 'package:melos_core/core/navigation/navigator.dart';

import '../../screens/chats_screen.dart';
import 'chat_report_sheet.dart';

class ChatReportButton extends StatelessWidget {
  const ChatReportButton({super.key});

  Future<void> _showReportSheet(BuildContext context) async {
    final bool? submitted = await showModalBottomSheet<bool>(
      context: context,
      isScrollControlled: true,
      useSafeArea: true,
      backgroundColor: AppColors.transparent,
      barrierColor: AppColors.blackAlpha50,
      builder: (_) => const ChatReportSheet(),
    );
    if (submitted == true && context.mounted) Go.off(const ChatListScreen());
  }

  @override
  Widget build(BuildContext context) => IconButton(
    tooltip: LocaleKeys.chatReportProblemTitle,
    onPressed: () => _showReportSheet(context),
    icon: const Icon(Icons.more_vert_rounded),
  );
}
