import 'package:flutter/material.dart';
import '../app_control_theme.dart';
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
  final ValueNotifier<bool> _isLoading = ValueNotifier(false);

  @override
  void dispose() {
    _isLoading.dispose();
    super.dispose();
  }

  Future<void> _asyncCall() async {
    if (_isLoading.value) return;
    _isLoading.value = true;
    try {
      await widget.call(context);
    } finally {
      if (mounted) _isLoading.value = false;
    }
  }

  @override
  Widget build(BuildContext context) {
    final bool grow = Theme.of(context).extension<AppControlTheme>() != null;
    return ValueListenableBuilder<bool>(
      valueListenable: _isLoading,
      builder: (context, loading, _) => Semantics(
        button: true,
        enabled: !loading,
        liveRegion: loading,
        child: SizedBox(
          width: widget.width,
          height: grow ? null : widget.height,
          child: ConstrainedBox(
            constraints: BoxConstraints(minHeight: widget.height),
            child: ElevatedButton(
              onPressed: loading ? null : _asyncCall,
              style: ElevatedButton.styleFrom(
                backgroundColor: widget.btnColor,
                disabledBackgroundColor: widget.btnColor,
                foregroundColor: AppColors.white,
                padding: EdgeInsets.symmetric(
                  horizontal: 16.w,
                  vertical: grow ? 12.h : 0,
                ),
                elevation: 0,
                shape: RoundedRectangleBorder(
                  borderRadius: BorderRadius.circular(widget.borderRadius),
                ),
              ),
              child: Stack(
                alignment: Alignment.center,
                children: [
                  // Retain the idle label's size and semantics while submitting.
                  Opacity(
                    opacity: loading ? 0 : 1,
                    alwaysIncludeSemantics: true,
                    child: widget.idleWidget,
                  ),
                  if (loading)
                    ExcludeSemantics(
                      child: SizedBox.square(
                        dimension: 24,
                        child: widget.loadingWidget,
                      ),
                    ),
                ],
              ),
            ),
          ),
        ),
      ),
    );
  }
}
