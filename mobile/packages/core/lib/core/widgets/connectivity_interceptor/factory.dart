 import 'package:internet_connection_checker/internet_connection_checker.dart';

class InternetCheck{
  late InternetConnectionChecker connectionChecker;
  late InternetConnectionStatus status;

  void init(){
    connectionChecker = InternetConnectionChecker.instance
      ..configure(slowConnectionConfig: const SlowConnectionConfig(enableToCheckForSlowConnection: true))
    ..checkTimeout = const Duration(seconds: 5);
  }

  Future<void> getInitialStatus()async{
    status = await _currentStatus;
  }

  void start(void Function(InternetConnectionStatus connectionStatus)? onChanged)async{
    connectionChecker.onStatusChange.listen(onChanged);
  }

  Future<void> stop()async{
    connectionChecker.dispose();
  }

  Future<InternetConnectionStatus> get _currentStatus async{
    return await connectionChecker.connectionStatus;
  }
}