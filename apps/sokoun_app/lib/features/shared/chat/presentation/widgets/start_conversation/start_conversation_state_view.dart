import 'package:flutter/material.dart';
import 'package:melos_core/config/res/config_imports.dart';

class StartConversationLoadingView extends StatelessWidget {
  const StartConversationLoadingView({super.key});

  @override
  Widget build(BuildContext context) {
    return const Center(
      child: CircularProgressIndicator(color: AppColors.sokoonTeal),
    );
  }
}
