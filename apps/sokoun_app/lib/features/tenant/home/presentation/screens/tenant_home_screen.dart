import 'package:flutter/material.dart';
import 'package:sokoun_app/shared_widgets/app_scaffold.dart';
import 'package:sokoun_app/shared_widgets/sokoun_layout.dart';
import '../widgets/tenant_widgets/tenant_home_content.dart';

class TenantHomeScreen extends StatelessWidget {
  const TenantHomeScreen({super.key});

  @override
  Widget build(BuildContext context) => AppScaffold(
    showBackButton: false,
    contentWidth: SokounContentWidth.wide,
    body: const SafeArea(child: TenantHomeContent()),
  );
}
