// import 'dart:async';
// import 'package:flutter/material.dart';
// import 'factory.dart';
// import '../interface.dart';
// class InternetConnectionCheckerPackage extends InternetInterceptorWidget {
//
//   InternetConnectionCheckerPackage({super.key,
//     super.loadingWidget,
//     super.onInitialStatusBuilder,
//     required super.onChanged,
//     required super.builder,
//   });
//
//   late InternetCheck internetCheck;
//
//   final ValueNotifier<bool> _loading = ValueNotifier(false);
//   Future<void> _getInitialStatus()async{
//     _loading.value = true;
//     await internetCheck.getInitialStatus();
//     _loading.value = false;
//   }
//
//   Future<void> _init()async{
//     internetCheck = InternetCheck()..init();
//     await _getInitialStatus();
//     internetCheck.start((connectionStatus) {
//       flag = 1;
//       internetCheck.status = connectionStatus;
//       internetStreamController.add(internetCheck.status);
//       onChanged(internetCheck.status);
//     });
//   }
//
//   // @override
//   // void initState() {
//   //   _init();
//   //   super.initState();
//   // }
//
//   Widget get _buildInitialView{
//     if(onInitialStatusBuilder != null){
//       return onInitialStatusBuilder!(internetCheck.status);
//     }
//     return builder(internetCheck.status);
//   }
//
//   int flag = 0;
//   Widget get _buildStatusView{
//     if(flag == 0){
//       return _buildInitialView;
//     }else{
//       return builder(internetCheck.status);
//     }
//   }
//
//   // @override
//   // void dispose() {
//   //   internetCheck.stop();
//   //   super.dispose();
//   // }
//
//   Widget get _loadingWidget{
//     return loadingWidget?? const CircularProgressIndicator();
//   }
//
//   @override
//   Widget build(BuildContext context) {
//     return StreamBuilder(
//       stream: internetStreamController.stream,
//       builder: (context, snapshot) => _loading.value? Center(child: _loadingWidget) :
//       _buildStatusView,
//     );
//   }
// }