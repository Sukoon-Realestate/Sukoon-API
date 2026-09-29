import '../widgets/tenant_widgets/tenant_home_app_bar_title.dart';
import 'package:flutter/material.dart';
import 'package:sokoun_app/shared_widgets/app_scaffold.dart';
import 'package:sokoun_app/shared_widgets/sokoun_layout.dart';
import '../widgets/tenant_widgets/tenant_home_content.dart';

class TenantHomeScreen extends StatelessWidget {
  const TenantHomeScreen({super.key});

  @override
  Widget build(BuildContext context) => AppScaffold(
    titleWidget: const TenantHomeAppBarTitle(),
    showBackButton: false,
    toolbarHeight: 52 + MediaQuery.textScalerOf(context).scale(32),
    contentWidth: SokounContentWidth.wide,
    body: SafeArea(child: TenantHomeContent()),
  );
}
