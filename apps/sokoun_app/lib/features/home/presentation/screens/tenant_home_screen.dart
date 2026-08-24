import 'package:flutter/material.dart';
import 'package:melos_core/config/res/config_imports.dart';

import '../widgets/tenant_widgets/imports.dart';

class TenantHomeScreen extends StatelessWidget {
  const TenantHomeScreen({super.key});

  @override
  Widget build(BuildContext context) {
    return Directionality(
      textDirection: TextDirection.rtl,
      child: Scaffold(
        backgroundColor: AppColors.scaffoldBackground,
        body: SafeArea(
          child: TenantHomeContent(),
        ),
      ),
    );
  }
}
