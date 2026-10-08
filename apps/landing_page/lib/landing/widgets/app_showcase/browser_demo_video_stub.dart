import 'package:flutter/widgets.dart';

class BrowserDemoVideo extends StatelessWidget {
  const BrowserDemoVideo({required this.onFailureChanged, super.key});

  final ValueChanged<bool> onFailureChanged;

  @override
  Widget build(BuildContext context) => const SizedBox.shrink();
}
