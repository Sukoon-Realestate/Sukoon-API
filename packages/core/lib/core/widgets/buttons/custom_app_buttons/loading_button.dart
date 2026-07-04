import 'package:flutter/material.dart';
import 'package:easy_loading_button/easy_loading_button.dart';

import '../../../../config/res/config_imports.dart';
import '../../app_text.dart';

class LoadingButton extends StatelessWidget {
  final Future<void> Function(BuildContext context) call;
  final Color btnColor;
  final double borderRadius;
  final double height;
  final double width;
  final double contentGap;
  final Widget loadingWidget;
  final Widget idleWidget;

  LoadingButton({super.key,
    required this.call,
    this.btnColor = AppColors.primary,
    this.height = 40,
    this.borderRadius = 0.0,
    this.width = double.infinity,
    this.contentGap = 12,
    this.idleWidget = const AppText('Confirm'),
    required this.loadingWidget,
  });

  void _changeState(EasyButtonState state){
    _easyButtonState = state;
  }

  EasyButtonState _easyButtonState = EasyButtonState.idle;

  Future<void> asyncCall(BuildContext context)async{
    try {
      _changeState(EasyButtonState.loading);
      await call(context);
      _changeState(EasyButtonState.idle);

    } finally {
      _changeState(EasyButtonState.idle);
    }
  }

  @override
  Widget build(BuildContext context) {
    return EasyButton(
        state: _easyButtonState,
        buttonColor: btnColor,
        borderRadius: borderRadius,
        contentGap: contentGap,
        height: height,
        width: width,
        useWidthAnimation: true,
        useEqualLoadingStateWidgetDimension: true,
        onPressed: () async=> await asyncCall(context),
        idleStateWidget: idleWidget,
        loadingStateWidget: SizedBox.square(
            dimension: 20,
            child: loadingWidget
        )
    );
  }
}

// import 'dart:async';
// import 'dart:developer';
// import 'dart:developer';
// import 'dart:developer';
// import 'dart:developer';
// import 'dart:developer';
// import 'dart:developer';
// import 'dart:developer';
// import 'dart:developer';
// import 'package:flutter/cupertino.dart';
// import 'package:flutter/material.dart';
// import 'package:flutter_screenutil/flutter_screenutil.dart';
// import 'dart:ui' show lerpDouble;
// import '../../../../config/res/config_imports.dart';
//
// class LoadingButton extends StatelessWidget {
//   final String? title;
//   final FutureOr<void> Function() onTap;
//   final Color? textColor;
//   final Color? color;
//   final BorderSide borderSide;
//   final double? borderRadius;
//   final EdgeInsets? margin;
//   final double? width;
//   final double? height;
//   final double? fontSize;
//   final String? fontFamily;
//   final Widget? customChild;
//   final FontWeight? fontWeight;
//
//   const LoadingButton({
//     super.key,
//     this.title,
//     this.customChild,
//     required this.onTap,
//     this.color,
//     this.textColor,
//     this.borderRadius,
//     this.margin,
//     this.borderSide = BorderSide.none,
//     this.fontFamily,
//     this.fontSize,
//     this.width,
//     this.height,
//     this.fontWeight,
//   }) : assert(title != null || customChild != null);
//
//   @override
//   Widget build(BuildContext context) {
//     return Center(
//       child: SizedBox(
//         height: height,
//         child: CustomAnimatedButton(
//           onTap: onTap,
//           width: width ?? MediaQuery.sizeOf(context).width,
//           minWidth: AppSize.sW50,
//           height: 35.h,
//           color: color ?? AppColors.primary,
//           borderRadius: borderRadius ?? AppSize.sH10,
//           disabledColor: color ?? AppColors.primary,
//           borderSide: borderSide,
//           loader: const CupertinoActivityIndicator(
//             color: Colors.white,
//           ),
//           child: title != null
//               ? Text(
//             title!,
//             style: TextStyle(
//                 fontFamily: ConstantManager.fontFamily,
//                 color: textColor ?? Colors.white,
//                 fontSize: fontSize ?? FontSize.s14,
//                 fontWeight: FontWeight.bold),
//           )
//               : customChild!,
//         ),
//       ),
//     );
//   }
// }
//
//
// enum ButtonStatus { loading, idle }
//
// class CustomAnimatedButton extends StatefulWidget {
//   final double height;
//   final double width;
//   final double minWidth;
//   final Widget? loader;
//   final Duration animationDuration;
//   final Curve curve;
//   final Curve reverseCurve;
//   final Widget child;
//   final FutureOr<void> Function() onTap;
//   final Color? color;
//   final Brightness? colorBrightness;
//   final double? elevation;
//   final EdgeInsetsGeometry padding;
//   final Clip clipBehavior;
//   final FocusNode? focusNode;
//   final MaterialTapTargetSize? materialTapTargetSize;
//   final bool roundLoadingShape;
//   final double borderRadius;
//   final BorderSide borderSide;
//   final double? disabledElevation;
//   final Color? disabledColor;
//   final Color? disabledTextColor;
//
//   const CustomAnimatedButton({
//     required this.height,
//     required this.width,
//     this.minWidth = 0,
//     this.loader,
//     this.animationDuration = const Duration(milliseconds: 500),
//     this.curve = Curves.easeInOutCirc,
//     this.reverseCurve = Curves.easeInOutCirc,
//     required this.child,
//     required this.onTap,
//     this.color,
//     this.colorBrightness,
//     this.elevation,
//     this.padding = const EdgeInsets.all(0),
//     this.borderRadius = 0.0,
//     this.clipBehavior = Clip.none,
//     this.focusNode,
//     this.materialTapTargetSize,
//     this.roundLoadingShape = true,
//     this.borderSide = BorderSide.none,
//     this.disabledElevation,
//     this.disabledColor,
//     this.disabledTextColor,
//     super.key,
//   })  : assert(elevation == null || elevation >= 0.0),
//         assert(disabledElevation == null || disabledElevation >= 0.0);
//
//   @override
//   CustomButtonState createState() => CustomButtonState();
// }
//
// class CustomButtonState extends State<CustomAnimatedButton>
//     with TickerProviderStateMixin {
//   double? loaderWidth;
//
//   late Animation<double> _animation;
//   late AnimationController _controller;
//   ButtonStatus buttonStatus = ButtonStatus.idle;
//
//   double _minWidth = 0;
//
//   @override
//   void initState() {
//     super.initState();
//
//     _controller =
//         AnimationController(vsync: this, duration: widget.animationDuration);
//
//     _animation = Tween(begin: 0.0, end: 1.0).animate(CurvedAnimation(
//         parent: _controller,
//         curve: widget.curve,
//         reverseCurve: widget.reverseCurve));
//
//     _animation.addStatusListener((status) {
//       if (status == AnimationStatus.dismissed) {
//         setState(() {
//           buttonStatus = ButtonStatus.idle;
//         });
//       }
//     });
//
//     minWidth = widget.height;
//     loaderWidth = widget.height;
//   }
//
//   @override
//   void dispose() {
//     _controller.dispose();
//     super.dispose();
//   }
//
//   void startLoading() {
//     log('⏺️ startLoading: Setting state to loading');
//     setState(() {
//       buttonStatus = ButtonStatus.loading;
//     });
//     log('▶️ startLoading: Forwarding animation controller');
//     _controller.forward();
//   }
//
//   void stopLoading() {
//     _controller.reverse();
//   }
//
//   lerpWidth(a, b, t) {
//     if (a == 0.0 || b == 0.0) {
//       return null;
//     } else {
//       return a + (b - a) * t;
//     }
//   }
//
//   double get minWidth => _minWidth;
//
//   set minWidth(double w) {
//     if (widget.minWidth == 0) {
//       _minWidth = w;
//     } else {
//       _minWidth = widget.minWidth;
//     }
//   }
//
//   @override
//   Widget build(BuildContext context) {
//     return AnimatedBuilder(
//       animation: _controller,
//       builder: (context, child) {
//         return _buildButton();
//       },
//     );
//   }
//
//   void doWhileLoading() async {
//     try {
//       log('🔵 doWhileLoading: Starting');
//       startLoading();
//       log('🟢 doWhileLoading: Loading started, awaiting onTap');
//
//       // Ensure minimum loading duration of 500ms to show animation
//
//       await widget.onTap();
//
//       log('🟡 doWhileLoading: onTap completed');
//     } catch (e) {
//       log('🔴 doWhileLoading: Error - $e');
//       rethrow;
//     } finally {
//       log('⚫ doWhileLoading: Stopping loading');
//       stopLoading();
//     }
//   }
//
//   Widget _buildButton() {
//     log('🎨 Building button with status: $buttonStatus, animation: ${_animation.value}');
//     return SizedBox(
//       height: widget.height,
//       width: lerpWidth(widget.width, minWidth, _animation.value),
//       child: ButtonTheme(
//         height: widget.height,
//         shape: RoundedRectangleBorder(
//           side: widget.borderSide,
//           borderRadius: BorderRadius.circular(widget.roundLoadingShape
//               ? lerpDouble(
//             widget.borderRadius,
//             widget.height / 2,
//             _animation.value,
//           )!
//               : widget.borderRadius),
//         ),
//         child: ElevatedButton(
//             style: ElevatedButton.styleFrom(
//               backgroundColor: widget.color,
//               elevation: widget.elevation,
//               padding: widget.padding,
//               disabledBackgroundColor: widget.disabledColor ?? AppColors.black,
//               shape: RoundedRectangleBorder(
//                 side: widget.borderSide,
//                 borderRadius: BorderRadius.circular(widget.roundLoadingShape
//                     ? lerpDouble(widget.borderRadius, widget.height / 2,
//                     _animation.value)!
//                     : widget.borderRadius),
//               ),
//             ),
//             clipBehavior: widget.clipBehavior,
//             focusNode: widget.focusNode,
//             onPressed: buttonStatus == ButtonStatus.idle
//                 ? () {
//               doWhileLoading();
//             }
//                 : null,
//             child: buttonStatus == ButtonStatus.idle
//                 ? widget.child
//                 : widget.loader),
//       ),
//     );
//   }
// }
//
