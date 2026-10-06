import 'package:flutter/material.dart';
import 'package:melos_core/config/language/locale_keys.g.dart';
import 'package:melos_core/core/widgets/app_text.dart';
import 'package:melos_core/core/widgets/buttons/app_loading_button.dart';

class OwnerDraftSaveWarning extends StatelessWidget {
  const OwnerDraftSaveWarning({super.key, required this.onRetry});
  final Future<void> Function() onRetry;

  @override
  Widget build(BuildContext context) => Padding(
    padding: const EdgeInsets.all(16),
    child: Column(
      crossAxisAlignment: CrossAxisAlignment.stretch,
      children: [
        AppText(LocaleKeys.freeLocalSaveFailed),
        const SizedBox(height: 8),
        AppLoadingButton(
          title: LocaleKeys.ownerRetryAction,
          asyncCall: (_) => onRetry(),
        ),
      ],
    ),
  );
}
