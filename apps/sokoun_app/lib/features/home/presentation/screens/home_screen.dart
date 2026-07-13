import 'package:flutter/material.dart';
import 'package:melos_core/core/helpers/user_type/user_enum.dart';
import 'package:melos_core/core/helpers/user_type/user_type_helper.dart';

import 'owner_home_screen.dart';
import 'tenant_home_screen.dart';

class HomeScreen extends StatelessWidget {
  const HomeScreen({super.key});

  @override
  Widget build(BuildContext context) {
    return UserTypeHelper.instance.currentUserType.isOwner
        ? const OwnerHomeScreen()
        : const TenantHomeScreen();
  }
}
