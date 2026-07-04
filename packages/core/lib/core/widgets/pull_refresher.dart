import 'package:flutter/material.dart';

import '../../config/res/config_imports.dart';

class PullRefresherWidget extends StatelessWidget {
  final Widget child;
  final Future<void> Function() onRefresh;


  const PullRefresherWidget({super.key,
    required this.child,
    required this.onRefresh,
  });

  @override
  Widget build(BuildContext context) {
    return RefreshIndicator(
        onRefresh: onRefresh,
        color: AppColors.primary,
        backgroundColor: Colors.white,
        child: child
    );
  }
}
