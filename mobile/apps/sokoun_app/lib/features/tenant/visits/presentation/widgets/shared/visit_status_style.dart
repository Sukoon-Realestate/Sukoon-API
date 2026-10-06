import 'package:flutter/material.dart';
import 'package:melos_core/config/res/config_imports.dart';

import '../../../data/enums/visit_status.dart';

extension VisitStatusStyle on TenantVisitStatus {
  Color get foregroundColor => switch (this) {
    TenantVisitStatus.accepted ||
    TenantVisitStatus.completed => AppColors.greenStrong,
    TenantVisitStatus.pending => AppColors.brown,
    TenantVisitStatus.rejected => AppColors.sokoonRose,
    TenantVisitStatus.canceled => AppColors.sokoonGray,
  };

  Color get backgroundColor => switch (this) {
    TenantVisitStatus.accepted ||
    TenantVisitStatus.completed => AppColors.greenPale,
    TenantVisitStatus.pending => AppColors.amberPale,
    TenantVisitStatus.rejected => AppColors.redPale,
    TenantVisitStatus.canceled => AppColors.grayBackground,
  };

  IconData get statusIcon => switch (this) {
    TenantVisitStatus.accepted ||
    TenantVisitStatus.completed => Icons.check_circle_outline_rounded,
    TenantVisitStatus.pending => Icons.schedule_rounded,
    TenantVisitStatus.rejected ||
    TenantVisitStatus.canceled => Icons.cancel_outlined,
  };
}
