import 'package:flutter/material.dart';

class CustomShimmer extends StatefulWidget {
  const CustomShimmer({
    required this.child,
    this.baseColor,
    this.highlightColor,
    this.duration = const Duration(milliseconds: 1400),
    super.key,
  });

  final Widget child;
  final Color? baseColor;
  final Color? highlightColor;
  final Duration duration;

  @override
  State<CustomShimmer> createState() => _CustomShimmerState();
}

class _CustomShimmerState extends State<CustomShimmer>
    with SingleTickerProviderStateMixin {
  late final AnimationController _controller;

  @override
  void initState() {
    super.initState();
    _controller = AnimationController(vsync: this, duration: widget.duration);
  }

  @override
  void didChangeDependencies() {
    super.didChangeDependencies();
    if (MediaQuery.disableAnimationsOf(context)) {
      _controller.stop();
    } else if (!_controller.isAnimating) {
      _controller.repeat();
    }
  }

  @override
  void didUpdateWidget(CustomShimmer oldWidget) {
    super.didUpdateWidget(oldWidget);
    if (oldWidget.duration != widget.duration) {
      _controller.duration = widget.duration;
      if (!MediaQuery.disableAnimationsOf(context)) {
        _controller.repeat();
      }
    }
  }

  @override
  void dispose() {
    _controller.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final bool isDark = Theme.of(context).brightness == Brightness.dark;
    final Color baseColor =
        widget.baseColor ??
        (isDark ? Colors.grey.shade800 : Colors.grey.shade300);
    final Color highlightColor =
        widget.highlightColor ??
        (isDark ? Colors.grey.shade600 : Colors.grey.shade100);

    return IgnorePointer(
      child: ExcludeSemantics(
        child: AnimatedBuilder(
          animation: _controller,
          child: widget.child,
          builder: (context, child) {
            final double position = (_controller.value * 2) - 1;
            return ShaderMask(
              blendMode: BlendMode.srcATop,
              shaderCallback: (bounds) => LinearGradient(
                begin: Alignment(position - 1, -0.3),
                end: Alignment(position + 1, 0.3),
                colors: [baseColor, highlightColor, baseColor],
                stops: const [0, 0.5, 1],
              ).createShader(bounds),
              child: child,
            );
          },
        ),
      ),
    );
  }
}
