import 'dart:async';
import 'package:flutter/material.dart';
import 'package:internet_connection_checker/internet_connection_checker.dart';
import 'factory.dart';

class InternetInterceptorWidget extends StatefulWidget {
  final Widget? loadingWidget;
  final bool rebuildWhenInternetRestored;
  final FutureOr<void> Function(InternetConnectionStatus previousStatus, InternetConnectionStatus connectionStatus) onChanged;
  final Widget Function(InternetConnectionStatus previousStatus, InternetConnectionStatus connectionStatus) builder;
  final Widget Function(InternetConnectionStatus connectionStatus)? onInitialStatusBuilder;

  const InternetInterceptorWidget({super.key,
    this.loadingWidget,
    required this.onChanged,
    required this.builder,
    this.onInitialStatusBuilder,
    this.rebuildWhenInternetRestored = false,
  });

  @override
  State<InternetInterceptorWidget> createState() => _InternetInterceptorWidgetState();
}

class _InternetInterceptorWidgetState extends State<InternetInterceptorWidget>
    with WidgetsBindingObserver{


  @override
  void didChangeAppLifecycleState(AppLifecycleState state) {
    if(state == AppLifecycleState.paused){
      _stop();

    }else{
      _start();
    }
    super.didChangeAppLifecycleState(state);
  }

  late InternetCheck internetCheck;
  late InternetConnectionStatus previousState = InternetConnectionStatus.disconnected;

  bool _loading = false;
  Future<void> _getInitialStatus()async{
    setState(() => _loading = true);
    await internetCheck.getInitialStatus();
    setState(() => _loading = false);
  }

  void _start(){
    internetCheck.start((connectionStatus) =>
        setState(() {
          flag = 1;
          widget.onChanged(previousState, connectionStatus);
          previousState = internetCheck.status;
          internetCheck.status = connectionStatus;
        })
    );
  }

  Future<void> _init()async{
    internetCheck = InternetCheck()..init();
    await _getInitialStatus();
    _start();
  }

  @override
  void initState() {
    _init();
    WidgetsBinding.instance.addObserver(this);
    super.initState();
  }

  Widget get _buildInitialView{
    if(widget.onInitialStatusBuilder != null){
      return widget.onInitialStatusBuilder!(internetCheck.status);
    }
    return widget.builder(previousState, internetCheck.status);
  }

  int flag = 0;
  Widget get _buildStatusView{
    if(flag == 0){
      return _buildInitialView;

    }else{
      return widget.builder(previousState, internetCheck.status);
    }
  }

  void _stop() => internetCheck.stop();

  @override
  void dispose() {
    _stop();
    WidgetsBinding.instance.removeObserver(this);
    super.dispose();
  }

  Widget get _loadingWidget{
    return widget.loadingWidget?? const CircularProgressIndicator();
  }
  @override
  Widget build(BuildContext context) {
    return _loading? Center(child: _loadingWidget) :
    _buildStatusView;
  }
}



// import 'dart:async';
// import 'package:flutter/material.dart';
// import 'package:internet_connection_checker/internet_connection_checker.dart';
// import '../../helpers/app_life_sycle_interceptor.dart';
// import 'factory.dart';
// class InternetInterceptorWidget extends StatefulWidget {
//   final Widget? loadingWidget;
//   final FutureOr<void> Function(InternetConnectionStatus connectionStatus) onChanged;
//   final Widget Function(InternetConnectionStatus connectionStatus) builder;
//   final Widget Function(InternetConnectionStatus connectionStatus)? onInitialStatusBuilder;
//
//   const InternetInterceptorWidget({super.key,
//     this.loadingWidget,
//     required this.onChanged,
//     required this.builder,
//     this.onInitialStatusBuilder,
//   });
//
//   @override
//   State<InternetInterceptorWidget> createState() => _InternetInterceptorWidgetState();
// }
//
// class _InternetInterceptorWidgetState extends State<InternetInterceptorWidget> {
//
//   late InternetCheck internetCheck;
//
//   bool _loading = false;
//   Future<void> _getInitialStatus()async{
//     setState(() => _loading = true);
//     await internetCheck.getInitialStatus();
//     setState(() => _loading = false);
//   }
//
//   Future<void> _init()async{
//     internetCheck = InternetCheck()..init();
//     await _getInitialStatus();
//
//     internetCheck.start((connectionStatus) =>
//         setState(() {
//           flag = 1;
//           widget.onChanged(connectionStatus);
//           internetCheck.status = connectionStatus;
//         })
//     );
//   }
//
//   @override
//   void initState() {
//     _init();
//     super.initState();
//   }
//
//   Widget get _buildInitialView{
//     if(widget.onInitialStatusBuilder != null){
//       return widget.onInitialStatusBuilder!(internetCheck.status);
//     }
//     return widget.builder(internetCheck.status);
//   }
//
//   int flag = 0;
//   Widget get _buildStatusView{
//     if(flag == 0){
//       return _buildInitialView;
//
//     }else{
//       return widget.builder(internetCheck.status);
//     }
//   }
//
//   @override
//   void dispose() {
//     internetCheck.stop();
//     super.dispose();
//   }
//
//   Widget get _loadingWidget{
//     return widget.loadingWidget?? const CircularProgressIndicator();
//   }
//   @override
//   Widget build(BuildContext context) {
//     return _loading? Center(child: _loadingWidget) :
//     _buildStatusView;
//   }
// }
