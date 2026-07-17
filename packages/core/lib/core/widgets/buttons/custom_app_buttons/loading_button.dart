import 'package:flutter/material.dart';
import 'package:easy_loading_button/easy_loading_button.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';
import '../../../../config/res/config_imports.dart';
import '../../app_text.dart';

class LoadingButton extends StatefulWidget {
  final Future<void> Function(BuildContext context) call;
  final Color btnColor;
  final double borderRadius;
  final double height;
  final double width;
  final double contentGap;
  final Widget loadingWidget;
  final Widget idleWidget;

  const LoadingButton({
    super.key,
    required this.call,
    this.btnColor = AppColors.primary,
    this.height = 40,
    this.borderRadius = 0.0,
    this.width = double.infinity,
    this.contentGap = 12,
    this.idleWidget = const AppText('Confirm'),
    required this.loadingWidget,
  });

  @override
  State<LoadingButton> createState() => _LoadingButtonState();
}

class _LoadingButtonState extends State<LoadingButton> {
  bool get _isLoading => _buttonState == EasyButtonState.loading;
  EasyButtonState _buttonState = EasyButtonState.idle;
  Future<void> _asyncCall(BuildContext context) async {
    _buttonState = EasyButtonState.loading;
    try {
      await widget.call(context);
    } finally {
      _buttonState = EasyButtonState.idle;
    }
  }

  Color get _buttonColor => _isLoading?
  Colors.grey[200]! : widget.btnColor;

  @override
  Widget build(BuildContext context) {
    return EasyButton(
      state: _buttonState,
      buttonColor: _buttonColor,
      borderRadius: widget.borderRadius,
      contentGap: widget.contentGap,
      height: widget.height,
      width: widget.width,
      useWidthAnimation: false,
      useEqualLoadingStateWidgetDimension: false,
      onPressed: () async => await _asyncCall(context),
      idleStateWidget: widget.idleWidget,
      loadingStateWidget: SizedBox.square(
        dimension: 25.sp,
        child: widget.loadingWidget,
      ),
    );
  }
}
