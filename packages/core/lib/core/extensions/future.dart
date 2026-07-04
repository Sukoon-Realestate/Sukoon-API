import 'dart:async';
import 'dart:developer';
import 'package:multiple_result/multiple_result.dart';

extension FutureTimer<T> on Future<T>{

  void _handleStoppingTimer({
    required Duration duration, required Timer time,
    required FutureOr<void> Function()? onFinish
  }){
    if(duration.inSeconds == time.tick){
      _cancelAndFinish(time: time, onFinish: onFinish);
      return;
    }
  }

  void  _handleMakingActionEvery(Duration actionEvery, Timer time, {
    required FutureOr<void> Function(int seconds, int triesNumber) handling
  }){
    if(time.tick % actionEvery.inSeconds == 0){
      handling.call(time.tick, (time.tick / actionEvery.inSeconds).toInt());
    }
  }

  void _cancelAndFinish({
    required Timer time,
    required FutureOr<void> Function()? onFinish,
  }){
    time.cancel();
    onFinish?.call();
    log('stop timer and finish process...');
  }

  void startTimer(Duration duration, {
    required Duration actionEvery,
    required FutureOr<void> Function(int seconds, int triesNumber) onActionEveryTriggered,
    FutureOr<void> Function(int seconds)? onTimeChanged,
    FutureOr<void> Function()? onFinish,
  })async{
    Timer.periodic(const Duration(seconds: 1), (time){
      whenComplete(() =>
          _cancelAndFinish(
              time: time,
              onFinish: onFinish
          )
      );
      _handleStoppingTimer(
          duration: duration,
          time: time,
          onFinish: onFinish
      );
      onTimeChanged?.call(time.tick);
      _handleMakingActionEvery(
          actionEvery,
          time,
          handling: onActionEveryTriggered
      );
    });
  }

  // debug
  Future<void> measureTime({void Function(Duration duration)? onEnd}) async {
    final start = DateTime.now();
    await this;
    final end = DateTime.now();
    onEnd?.call(end.difference(start));
  }

  Future<T> delayBefore(Duration duration) async {
    await Future.delayed(duration);
    return await this;
  }
}

extension FutureHelpers<T,E> on Future<Result<T,E>>{
  Future<void> when({
    FutureOr<void> Function()? onLoading,
    FutureOr<void> Function(T data)? onSuccess,
    FutureOr<void> Function(E error)? onError,
  })async{
    onLoading?.call();
    final result = await this;
    result.when(
            (T data) => onSuccess?.call(data),
            (E error) => onError?.call(error)
    );
  }
}

extension FutureDebouncer<T> on Future<T>{
  // static void run({
  //   Duration? duration,
  //   required void Function() action
  // }){
  //   EasyDebounce.debounce(
  //     'debouncer',
  //     duration?? Duration(milliseconds: 500),
  //         () => action.call(),
  //   );
  // }
}

// mixin AutoTimerCloser<T extends StatefulWidget> on State<T>, RouteAware {
//
//   final RouteObserver<PageRoute> routeObserver = RouteObserver<PageRoute>();
//   final ValueKey timerKey = ValueKey(T);
//
//   @override
//   void didChangeDependencies() {
//     super.didChangeDependencies();
//     routeObserver.subscribe(this, ModalRoute.of(context)! as PageRoute);
//   }
//
//   @override
//   void dispose() {
//     routeObserver.unsubscribe(this);
//     super.dispose();
//   }
//
//   @override
//   void didPopNext() {}
//
//   @override
//   void didPushNext() {
//     // 🔥 Automatically close the timer when navigating away
//     FutureTimer.closeTimer(timerKey);
//   }
//
//   @override
//   void didPop() {
//     // 🔥 Also close it when this screen is popped
//     FutureTimer.closeTimer(timerKey);
//   }
// }