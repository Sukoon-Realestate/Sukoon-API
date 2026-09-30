import 'dart:async';
import 'package:flutter/material.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';
import 'package:melos_core/config/language/locale_keys.g.dart';
import 'package:melos_core/config/res/config_imports.dart';
import 'package:melos_core/core/helpers/text_style_manager.dart';
import 'package:melos_core/core/shared/route_observer.dart';
import 'package:melos_core/core/widgets/app_text.dart';
import 'package:video_player/video_player.dart';

typedef _Playback = ({
  bool loading,
  bool failed,
  VideoPlayerController? controller,
});

class PropertyVideo extends StatefulWidget {
  const PropertyVideo({super.key, required this.url, this.durationSeconds});
  final String url;
  final int? durationSeconds;
  @override
  State<PropertyVideo> createState() => _PropertyVideoState();
}

class _PropertyVideoState extends State<PropertyVideo>
    with WidgetsBindingObserver, RouteAware {
  final ValueNotifier<_Playback> _playback = ValueNotifier((
    loading: false,
    failed: false,
    controller: null,
  ));
  VideoPlayerController? _controller;
  ModalRoute<dynamic>? _route;
  int _generation = 0;

  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addObserver(this);
  }

  @override
  void didChangeDependencies() {
    super.didChangeDependencies();
    final route = ModalRoute.of(context);
    if (_route != route) {
      AppNavigationObserver.instance.unsubscribe(this);
      _route = route;
      if (route != null) AppNavigationObserver.instance.subscribe(this, route);
    }
  }

  @override
  void didUpdateWidget(covariant PropertyVideo oldWidget) {
    super.didUpdateWidget(oldWidget);
    if (oldWidget.url != widget.url) {
      _generation++;
      unawaited(_controller?.dispose());
      _controller = null;
      _playback.value = (loading: false, failed: false, controller: null);
    }
  }

  @override
  void didPushNext() => unawaited(_pause());
  @override
  void didChangeAppLifecycleState(AppLifecycleState state) {
    if (state != AppLifecycleState.resumed) unawaited(_pause());
  }

  @override
  void dispose() {
    _generation++;
    AppNavigationObserver.instance.unsubscribe(this);
    WidgetsBinding.instance.removeObserver(this);
    unawaited(_controller?.dispose());
    _playback.dispose();
    super.dispose();
  }

  Future<void> _pause() async {
    final controller = _controller;
    try {
      await controller?.pause();
    } catch (_) {
      _showPlaybackError(controller);
    }
  }

  void _showPlaybackError(VideoPlayerController? controller) {
    if (mounted && identical(controller, _controller)) {
      _playback.value = (loading: false, failed: true, controller: null);
    }
  }

  Future<void> _toggle() async {
    if (_playback.value.loading) return;
    final VideoPlayerController? existing = _controller;
    if (existing != null &&
        existing.value.isInitialized &&
        !existing.value.hasError &&
        !_playback.value.failed) {
      try {
        if (existing.value.isPlaying) {
          await existing.pause();
        } else {
          if (existing.value.position >= existing.value.duration) {
            await existing.seekTo(Duration.zero);
          }
          if (mounted && identical(existing, _controller)) {
            await existing.play();
          }
        }
      } catch (_) {
        _showPlaybackError(existing);
      }
      return;
    }
    final int generation = ++_generation;
    _playback.value = (loading: true, failed: false, controller: null);
    if (existing != null) await existing.dispose();
    if (!mounted || generation != _generation) return;
    final Uri? uri = Uri.tryParse(widget.url);
    if (uri == null ||
        !['https', 'http'].contains(uri.scheme) ||
        uri.host.isEmpty) {
      _controller = null;
      _playback.value = (loading: false, failed: true, controller: null);
      return;
    }
    final VideoPlayerController controller = VideoPlayerController.networkUrl(
      uri,
    );
    _controller = controller;
    try {
      await controller.initialize();
      if (!mounted || generation != _generation) return;
      _playback.value = (loading: false, failed: false, controller: controller);
      final lifecycle = WidgetsBinding.instance.lifecycleState;
      if ((_route?.isCurrent ?? true) &&
          (lifecycle == null || lifecycle == AppLifecycleState.resumed)) {
        await controller.play();
      }
    } catch (_) {
      if (mounted && generation == _generation) {
        _playback.value = (loading: false, failed: true, controller: null);
      }
    }
  }

  @override
  Widget build(BuildContext context) => ValueListenableBuilder<_Playback>(
    valueListenable: _playback,
    builder: (_, playback, __) {
      final VideoPlayerController? controller = playback.controller;
      if (controller != null) {
        return ValueListenableBuilder<VideoPlayerValue>(
          valueListenable: controller,
          builder: (_, value, __) => _PropertyVideoSurface(
            durationSeconds: widget.durationSeconds ?? value.duration.inSeconds,
            onPressed: _toggle,
            isPlaying: value.isPlaying,
            loading: value.isBuffering,
            failed: value.hasError,
            child: value.hasError
                ? null
                : AspectRatio(
                    aspectRatio: value.aspectRatio > 0
                        ? value.aspectRatio
                        : 16 / 9,
                    child: VideoPlayer(controller),
                  ),
          ),
        );
      }
      return _PropertyVideoSurface(
        durationSeconds: widget.durationSeconds,
        onPressed: playback.loading ? null : _toggle,
        loading: playback.loading,
        failed: playback.failed,
      );
    },
  );
}

class _PropertyVideoSurface extends StatelessWidget {
  const _PropertyVideoSurface({
    required this.onPressed,
    required this.durationSeconds,
    this.loading = false,
    this.failed = false,
    this.isPlaying = false,
    this.child,
  });
  final VoidCallback? onPressed;
  final int? durationSeconds;
  final bool loading;
  final bool failed;
  final bool isPlaying;
  final Widget? child;
  @override
  Widget build(BuildContext context) {
    final int seconds = durationSeconds ?? 0;
    final String duration =
        '${seconds ~/ 60}:${(seconds % 60).toString().padLeft(2, '0')}';
    return Column(
      crossAxisAlignment: CrossAxisAlignment.stretch,
      children: [
        AppText(
          LocaleKeys.ownerPropertyVideoTitle,
          style: AppTextStyles.bold16,
        ),
        ClipRRect(
          borderRadius: BorderRadius.circular(12.r),
          child: ColoredBox(
            color: AppColors.sokoonNavy,
            child: Stack(
              alignment: Alignment.center,
              children: [
                child ??
                    AspectRatio(
                      aspectRatio: 16 / 9,
                      child: Icon(
                        Icons.videocam_outlined,
                        color: AppColors.grayPale,
                        size: 48.r,
                      ),
                    ),
                if (loading)
                  const CircularProgressIndicator(color: AppColors.white)
                else
                  IconButton.filled(
                    tooltip: failed
                        ? LocaleKeys.propertyVideoError
                        : isPlaying
                        ? LocaleKeys.propertyVideoPause
                        : LocaleKeys.propertyVideoPlay,
                    onPressed: onPressed,
                    icon: Icon(
                      failed
                          ? Icons.refresh_rounded
                          : isPlaying
                          ? Icons.pause_rounded
                          : Icons.play_arrow_rounded,
                    ),
                  ),
              ],
            ),
          ),
        ),
        if (seconds > 0)
          AppText(
            duration,
            style: AppTextStyles.regular12,
            textAlign: TextAlign.end,
          ),
        if (failed)
          TextButton(
            onPressed: onPressed,
            child: AppText(
              LocaleKeys.propertyVideoError,
              style: AppTextStyles.regular13,
            ),
          ),
      ],
    );
  }
}
