import 'package:connectivity_plus/connectivity_plus.dart';
import 'package:flutter/material.dart';
import 'interface.dart';

class ConnectivityHelper extends InternetInterceptorWidget{
  ConnectivityHelper({super.key,
    super.loadingWidget,
    super.onInitialStatusBuilder,
    required super.onChanged,
    required super.builder,
});

  late InternetStatus _internetStatus = InternetStatus.online;
  late final Connectivity _connectivity;

  final ValueNotifier<bool> _loading = ValueNotifier(false);
  // Future<void> _getInitialStatus()async{
  //   _loading.value = true;
  //   await internetCheck.getInitialStatus();
  //   _loading.value = false;
  // }

  InternetStatus _result(List<ConnectivityResult> data)  {
    if(data.contains(ConnectivityResult.none)){
      return InternetStatus.offline;

    }else{
      return InternetStatus.online;
    }
  }

  Future<void> init()async{
    _connectivity = Connectivity()..onConnectivityChanged.listen(
            (status) {
              flag = 1;
              _internetStatus = _result(status);
              internetStreamController.add(_internetStatus);
              onChanged(_internetStatus);
            }
    );
  }

  Widget get _buildInitialView{
    if(onInitialStatusBuilder != null){
      return onInitialStatusBuilder!(_internetStatus);
    }
    return builder(_internetStatus);
  }

  int flag = 0;
  Widget get _buildStatusView{
    if(flag == 0){
      return _buildInitialView;
    }else{
      return builder(_internetStatus);
    }
  }

  void dispose() {
  }

  Widget get _loadingWidget{
    return loadingWidget?? const CircularProgressIndicator();
  }

  @override
  Widget build(BuildContext context) {
    return StreamBuilder(
      stream: internetStreamController.stream,
      builder: (context, snapshot) => _loading.value? Center(child: _loadingWidget) :
      _buildStatusView,
    );
  }

}