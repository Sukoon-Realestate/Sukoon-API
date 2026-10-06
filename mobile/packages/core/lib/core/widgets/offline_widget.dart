// import 'dart:developer';
//
// import 'package:flutter/material.dart';
// import 'package:flutter_offline/flutter_offline.dart';
//
// import 'internet_exeption.dart';
//
// class OfflineWidget extends StatefulWidget {
//   final Widget child;
//   const OfflineWidget({super.key, required this.child});
//
//   @override
//   State<OfflineWidget> createState() => _OfflineWidgetState();
// }
//
// class _OfflineWidgetState extends State<OfflineWidget> {
//   bool connected = false;
//
//   @override
//   Widget build(BuildContext context) {
//     return OfflineBuilder(connectivityBuilder: (
//       BuildContext context,
//       List<ConnectivityResult> connectivity,
//       Widget item,
//     ) {
//       log('test $connectivity');
//       final bool notConnected = connectivity.contains(ConnectivityResult.none);
//       return Stack(
//         fit: StackFit.expand,
//         children: [
//           item,
//           if (notConnected) const InternetExpetion(),
//         ],
//       );
//     }, builder: (BuildContext context) {
//       log('test');
//       return widget.child;
//     }, errorBuilder: (BuildContext context) {
//       return const InternetExpetion();
//     }
//         // child: const SizedBox.shrink(),
//         );
//   }
// }
