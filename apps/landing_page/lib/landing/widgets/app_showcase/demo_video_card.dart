import 'package:flutter/foundation.dart';
import 'package:flutter/material.dart';
import 'package:melos_core/config/language/locale_keys.g.dart';
import 'package:video_player/video_player.dart';

import '../../theme/landing_theme.dart';
import 'browser_demo_video_stub.dart'
    if (dart.library.js_interop) 'browser_demo_video.dart';

class DemoVideoCard extends StatefulWidget {
  const DemoVideoCard({super.key});

  static const videoAsset = 'assets/videos/sokoun_demo.mp4';
  static const posterAsset = 'assets/images/sokoun_demo_poster.jpg';

  @override
  State<DemoVideoCard> createState() => _DemoVideoCardState();
}

class _DemoVideoCardState extends State<DemoVideoCard>
    with WidgetsBindingObserver {
  VideoPlayerController? _controller;
  bool _loading = false;
  bool _failed = false;
  bool _active = true;

  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addObserver(this);
  }

  @override
  void didChangeAppLifecycleState(AppLifecycleState state) {
    if (state != AppLifecycleState.resumed) _controller?.pause();
  }

  @override
  void deactivate() {
    _active = false;
    _controller?.pause();
    super.deactivate();
  }

  @override
  void activate() {
    super.activate();
    _active = true;
  }

  @override
  void dispose() {
    WidgetsBinding.instance.removeObserver(this);
    _controller?.removeListener(_handleVideoChanged);
    _controller?.dispose();
    super.dispose();
  }

  void _handleVideoChanged() {
    if (mounted && _active) {
      setState(() {
        if (_controller?.value.hasError ?? false) {
          _failed = true;
          _loading = false;
        }
      });
    }
  }

  Future<void> _play() async {
    if (_loading) return;
    final previous = _controller;
    if (previous != null && previous.value.isInitialized && !_failed) {
      if (previous.value.position >= previous.value.duration) {
        await previous.seekTo(Duration.zero);
      }
      await previous.play();
      return;
    }

    setState(() {
      _loading = true;
      _failed = false;
    });
    previous?.removeListener(_handleVideoChanged);
    await previous?.dispose();
    if (!mounted) return;
    final controller = VideoPlayerController.asset(DemoVideoCard.videoAsset);
    _controller = controller;
    controller.addListener(_handleVideoChanged);
    try {
      await controller.initialize();
      if (!mounted || controller != _controller) return;
      await controller.setVolume(0);
      await controller.play();
      if (mounted) setState(() => _loading = false);
    } catch (_) {
      if (mounted) {
        setState(() {
          _loading = false;
          _failed = true;
        });
      }
    }
  }

  String _time(Duration value) {
    final minutes = value.inMinutes;
    final seconds = (value.inSeconds % 60).toString().padLeft(2, '0');
    return '$minutes:$seconds';
  }

  @override
  Widget build(BuildContext context) {
    final controller = _controller;
    final initialized = controller?.value.isInitialized == true && !_failed;
    final playing = initialized && controller!.value.isPlaying;
    final value = controller?.value;
    final finished = initialized && value!.position >= value.duration;
    final duration = value?.duration ?? Duration.zero;

    return ConstrainedBox(
      constraints: const BoxConstraints(maxWidth: 1040),
      child: DecoratedBox(
        decoration: BoxDecoration(
          color: Colors.white,
          borderRadius: BorderRadius.circular(24),
          border: Border.all(color: LandingColors.border),
        ),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            if (kIsWeb)
              BrowserDemoVideo(
                onFailureChanged: (failed) {
                  if (mounted && _active && _failed != failed) {
                    setState(() => _failed = failed);
                  }
                },
              )
            else
              ClipRRect(
                borderRadius: const BorderRadius.vertical(
                  top: Radius.circular(24),
                ),
                child: AspectRatio(
                  aspectRatio: 16 / 9,
                  child: Semantics(
                    label: LocaleKeys.landingDemoVideoSemantic,
                    child: Stack(
                      fit: StackFit.expand,
                      children: [
                        Image.asset(
                          DemoVideoCard.posterAsset,
                          fit: BoxFit.cover,
                        ),
                        if (initialized) VideoPlayer(controller!),
                        if (!playing)
                          ColoredBox(
                            color: Colors.black.withValues(alpha: .18),
                            child: Center(
                              child: _loading
                                  ? Semantics(
                                      label: LocaleKeys.landingDemoLoading,
                                      child: const CircularProgressIndicator(
                                        color: Colors.white,
                                      ),
                                    )
                                  : FilledButton.icon(
                                      onPressed: _play,
                                      style: FilledButton.styleFrom(
                                        backgroundColor: LandingColors.teal,
                                        foregroundColor: Colors.white,
                                        padding: const EdgeInsets.symmetric(
                                          horizontal: 20,
                                          vertical: 16,
                                        ),
                                      ),
                                      icon: Icon(
                                        _failed
                                            ? Icons.refresh_rounded
                                            : finished
                                            ? Icons.replay_rounded
                                            : Icons.play_arrow_rounded,
                                      ),
                                      label: Text(
                                        _failed
                                            ? LocaleKeys.landingDemoRetry
                                            : finished
                                            ? LocaleKeys.landingDemoReplay
                                            : LocaleKeys.landingDemoPlay,
                                      ),
                                    ),
                            ),
                          ),
                      ],
                    ),
                  ),
                ),
              ),
            if (initialized)
              Padding(
                padding: const EdgeInsets.symmetric(
                  horizontal: 12,
                  vertical: 4,
                ),
                child: Directionality(
                  textDirection: TextDirection.ltr,
                  child: Row(
                    children: [
                      IconButton(
                        tooltip: playing
                            ? LocaleKeys.landingDemoPause
                            : LocaleKeys.landingDemoPlay,
                        color: LandingColors.teal,
                        onPressed: playing ? controller.pause : _play,
                        icon: Icon(
                          playing
                              ? Icons.pause_rounded
                              : Icons.play_arrow_rounded,
                        ),
                      ),
                      Expanded(
                        child: Slider(
                          semanticFormatterCallback: (milliseconds) =>
                              '${LocaleKeys.landingDemoSeek} ${_time(Duration(milliseconds: milliseconds.round()))}',
                          value: value!.position.inMilliseconds
                              .clamp(0, duration.inMilliseconds)
                              .toDouble(),
                          max: duration.inMilliseconds > 0
                              ? duration.inMilliseconds.toDouble()
                              : 1,
                          activeColor: LandingColors.teal,
                          onChanged: (position) => controller!.seekTo(
                            Duration(milliseconds: position.round()),
                          ),
                        ),
                      ),
                      Text(
                        '${_time(value.position)} / ${_time(duration)}',
                        style: const TextStyle(
                          fontSize: 12,
                          color: LandingColors.subtext,
                        ),
                      ),
                    ],
                  ),
                ),
              ),
            Padding(
              padding: const EdgeInsets.all(20),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    LocaleKeys.landingDemoTitle,
                    style: const TextStyle(
                      fontWeight: FontWeight.w800,
                      fontSize: 22,
                      color: LandingColors.navy,
                    ),
                  ),
                  const SizedBox(height: 8),
                  Text(
                    _failed
                        ? LocaleKeys.landingDemoError
                        : LocaleKeys.landingDemoDescription,
                    style: const TextStyle(
                      color: LandingColors.subtext,
                      height: 1.7,
                      fontSize: 15,
                    ),
                  ),
                  const SizedBox(height: 8),
                  ExpansionTile(
                    tilePadding: EdgeInsets.zero,
                    childrenPadding: const EdgeInsets.only(bottom: 12),
                    expandedCrossAxisAlignment: CrossAxisAlignment.start,
                    shape: const Border(),
                    collapsedShape: const Border(),
                    title: Text(
                      LocaleKeys.landingDemoTranscriptTitle,
                      style: const TextStyle(
                        fontSize: 14,
                        color: LandingColors.teal,
                      ),
                    ),
                    children: [
                      Text(
                        LocaleKeys.landingDemoTranscriptBody,
                        style: const TextStyle(
                          height: 1.8,
                          color: LandingColors.subtext,
                        ),
                      ),
                    ],
                  ),
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }
}
