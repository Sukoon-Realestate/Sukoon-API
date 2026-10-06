import 'package:flutter/material.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';
import 'package:melos_core/config/res/config_imports.dart';
import 'package:melos_core/generated/assets.dart';
import 'package:sokoun_app/shared_widgets/sokoun_motion.dart';

import 'splash_logo_sheen.dart';

class AnimatedSplashLogo extends StatefulWidget {
  const AnimatedSplashLogo({super.key, required this.onCompleted});

  final VoidCallback onCompleted;

  @override
  State<AnimatedSplashLogo> createState() => _AnimatedSplashLogoState();
}

class _AnimatedSplashLogoState extends State<AnimatedSplashLogo>
    with SingleTickerProviderStateMixin {
  late final AnimationController _controller = AnimationController(vsync: this)
    ..addStatusListener(_onAnimationStatusChanged);
  late final Animation<double> _opacity = _controller.drive(
    CurveTween(curve: const Interval(0, .32, curve: Curves.easeOutCubic)),
  );
  late final Animation<double> _entrance = _controller.drive(
    CurveTween(curve: const Interval(0, .58, curve: Curves.easeOutCubic)),
  );
  late final Animation<double> _scale = Tween<double>(
    begin: .9,
    end: 1,
  ).animate(_entrance);
  late final Animation<Offset> _position = Tween<Offset>(
    begin: const Offset(0, .045),
    end: Offset.zero,
  ).animate(_entrance);
  late final Animation<double> _sheen = _controller.drive(
    CurveTween(curve: const Interval(.4, .85, curve: Curves.easeInOutCubic)),
  );
  bool _preparingLogo = false;
  bool _logoReady = false;
  bool _completionScheduled = false;

  @override
  void didChangeDependencies() {
    super.didChangeDependencies();
    _controller.duration = SokounMotion.duration(context, milliseconds: 2000);
    if (!_preparingLogo) {
      _preparingLogo = true;
      _prepareLogo();
    } else if (_logoReady && _controller.duration == Duration.zero) {
      _controller.value = 1;
    }
  }

  Future<void> _prepareLogo() async {
    // Start the reveal only after the packaged image has been decoded.
    await precacheImage(
      Assets.png.logo.provider(package: 'melos_core'),
      context,
    );
    if (!mounted) return;
    _logoReady = true;
    if (_controller.duration == Duration.zero) {
      _controller.value = 1;
    } else {
      _controller.forward();
    }
  }

  void _onAnimationStatusChanged(AnimationStatus status) {
    if (status != AnimationStatus.completed || _completionScheduled) return;
    _completionScheduled = true;
    // Keep the final logo frame visible before startup can change routes.
    WidgetsBinding.instance.addPostFrameCallback((_) {
      if (mounted) widget.onCompleted();
    });
  }

  @override
  void dispose() {
    _controller.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return SafeArea(
      child: LayoutBuilder(
        builder: (context, constraints) {
          final double logoSize = (constraints.biggest.shortestSide * .78)
              .clamp(0.0, 320.r);

          return Center(
            child: FadeTransition(
              opacity: _opacity,
              child: SlideTransition(
                position: _position,
                child: ScaleTransition(
                  scale: _scale,
                  child: RepaintBoundary(
                    child: SizedBox.square(
                      dimension: logoSize,
                      child: SplashLogoSheen(
                        progress: _sheen,
                        child: Assets.png.logo.image(
                          package: 'melos_core',
                          fit: BoxFit.contain,
                          filterQuality: FilterQuality.high,
                          semanticLabel: ConstantManager.projectName,
                        ),
                      ),
                    ),
                  ),
                ),
              ),
            ),
          );
        },
      ),
    );
  }
}
