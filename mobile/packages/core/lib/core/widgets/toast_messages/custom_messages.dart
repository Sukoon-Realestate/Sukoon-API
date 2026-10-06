import 'package:flutter/material.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';
import 'package:top_snackbar_flutter/custom_snack_bar.dart';
import 'package:top_snackbar_flutter/top_snack_bar.dart';
import '../../../config/res/config_imports.dart';
import '../../navigation/navigator.dart';

enum MsgState{success, error, info}
class MessageUtils {
  static TextStyle get _textStyle => TextStyle(
      fontWeight: FontWeight.w600,
      fontSize: 16.sp,
      color: Colors.white,
      fontFamily: ConstantManager.fontFamily
  );

  // static void showTopMsg(String msg, {MsgState state = MsgState.error}){
  //   // final overlayState = Go.navigatorKey.currentState?.overlay;
  //   final overlayState = Overlay.of(Go.context);
  //   if(state == MsgState.success){
  //     showTopSnackBar(
  //       overlayState,
  //       CustomSnackBar.success(
  //         message: msg,
  //         messagePadding: EdgeInsets.all(10.r),
  //         textStyle: _textStyle
  //       )
  //     );
  //
  //   }else if(state == MsgState.error){
  //     showTopSnackBar(
  //       overlayState,
  //       CustomSnackBar.error(
  //           message: msg,
  //           messagePadding: EdgeInsets.all(10.r),
  //           textStyle: _textStyle
  //       ),
  //     );
  //
  //   }else{
  //     showTopSnackBar(
  //       overlayState,
  //       CustomSnackBar.info(
  //           message: msg,
  //           messagePadding: EdgeInsets.all(10.r),
  //           textStyle: _textStyle
  //       ),
  //     );
  //   }
  // }

  // static void showSnackBar(
  //   String message, {
  //   Color? backgroundColor,
  //   Color? textColor,
  //   BuildContext? context,
  // }) {
  //   final snackBar = SnackBar(
  //     duration: const Duration(seconds: ConstantManager.snackbarDuration),
  //     content: Text(
  //       message,
  //       style: TextStyle(
  //         color: textColor ?? Colors.red,
  //         fontSize: FontSize.s14,
  //       ),
  //     ),
  //     backgroundColor: backgroundColor ?? AppColors.white,
  //     behavior: SnackBarBehavior.floating,
  //   );
  //   ScaffoldMessenger.of(context ?? Go.context)
  //       .showSnackBar(snackBar);
  // }
}
