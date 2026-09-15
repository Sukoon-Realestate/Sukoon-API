import 'package:flutter/material.dart';
import 'package:melos_core/config/language/locale_keys.g.dart';
import 'package:melos_core/config/res/config_imports.dart';
import 'package:melos_core/core/widgets/app_text.dart';

class StartConversationLoadingView extends StatelessWidget {
  const StartConversationLoadingView({super.key});

  @override
  Widget build(BuildContext context) {
    return const Center(
      child: CircularProgressIndicator(color: AppColors.sokoonTeal),
    );
  }
}

class StartConversationErrorView extends StatelessWidget {
  const StartConversationErrorView({super.key, required this.onRetryPressed});

  final VoidCallback onRetryPressed;

  @override
  Widget build(BuildContext context) {
    return Center(
      child: TextButton.icon(
        onPressed: onRetryPressed,
        icon: const Icon(Icons.refresh_rounded, color: AppColors.sokoonTeal),
        label: AppText(LocaleKeys.operationFaild, color: AppColors.sokoonNavy),
      ),
    );
  }
}
