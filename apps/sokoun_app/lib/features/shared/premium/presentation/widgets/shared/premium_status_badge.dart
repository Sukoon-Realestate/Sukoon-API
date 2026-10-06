import 'package:flutter/material.dart';
import 'package:melos_core/core/widgets/app_text.dart';
import 'package:melos_core/config/res/config_imports.dart';
import '../../../data/enums/premium_status.dart';

class PremiumStatusBadge extends StatelessWidget {
  const PremiumStatusBadge({super.key, required this.status});
  final PremiumStatus status;
  @override
  Widget build(BuildContext context) {
    final color = switch (status) {
      PremiumStatus.active ||
      PremiumStatus.paid ||
      PremiumStatus.signed ||
      PremiumStatus.completed => context.appColor(AppColors.green),
      PremiumStatus.failed ||
      PremiumStatus.overdue => context.appColor(AppColors.sokoonRose),
      PremiumStatus.pending ||
      PremiumStatus.due => context.appColor(AppColors.amber),
      _ => context.appColor(AppColors.sokoonGray),
    };
    return Chip(
      side: BorderSide(color: color),
      label: AppText(status.label, color: color),
    );
  }
}
