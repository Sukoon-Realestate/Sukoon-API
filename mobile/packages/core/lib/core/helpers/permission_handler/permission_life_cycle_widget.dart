import 'package:flutter/material.dart';
import '../app_life_sycle_interceptor.dart';
import 'handler.dart' show PermissionHandler;
import 'model.dart' show PermissionModel;

class PermissionLifeCycleWidget extends StatefulWidget {
  final Widget child;
  final PermissionModel permissionManagerModel;
  const PermissionLifeCycleWidget({super.key,
    required this.child,
    required this.permissionManagerModel,
  });

  @override
  State<PermissionLifeCycleWidget> createState() => _PermissionLifeCycleWidgetState();
}

class _PermissionLifeCycleWidgetState extends State<PermissionLifeCycleWidget> {

  void _checkPermission()async{
    PermissionHandler().checkPermission(
        permissionManagerModel: widget.permissionManagerModel
    );
  }

  @override
  void initState() {
    _checkPermission();
    super.initState();
  }

  @override
  Widget build(BuildContext context) {
    return AppLifecycleManager(
      onResumed: () => _checkPermission(),
      child: widget.child,
    );
  }
}
