import 'dart:async';
import 'dart:js_interop';
import 'dart:ui_web' as ui_web;

import 'package:flutter/material.dart';
import 'package:melos_core/config/language/locale_keys.g.dart';
import 'package:web/web.dart' as web;

import '../../theme/landing_theme.dart';
import 'demo_video_card.dart';

/// Keep the media element attached before loading, and call play synchronously
/// from its native button. Slow downloads must not consume the user's gesture
/// while Flutter waits for the plugin's asynchronous initialization.
class BrowserDemoVideo extends StatefulWidget {
  const BrowserDemoVideo({required this.onFailureChanged, super.key});

  final ValueChanged<bool> onFailureChanged;

  @override
  State<BrowserDemoVideo> createState() => _BrowserDemoVideoState();
}

class _BrowserDemoVideoState extends State<BrowserDemoVideo>
    with WidgetsBindingObserver {
  final _subscriptions = <StreamSubscription<web.Event>>[];
  web.HTMLVideoElement? _video;
  web.HTMLButtonElement? _playButton;
  Timer? _loadTimer;
  bool _loading = false;
  bool _failed = false;
  bool _disposed = false;
  int _attempt = 0;

  String _assetUrl(String asset) => Uri.parse(
    web.document.baseURI,
  ).resolve(ui_web.assetManager.getAssetUrl(asset)).toString();

  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addObserver(this);
  }

  @override
  void didChangeAppLifecycleState(AppLifecycleState state) {
    if (state != AppLifecycleState.resumed) _pause();
  }

  void _pause() {
    _attempt++;
    _loadTimer?.cancel();
    _loading = false;
    _video?.pause();
    _updateButton();
  }

  @override
  void deactivate() {
    _pause();
    super.deactivate();
  }

  @override
  void dispose() {
    _disposed = true;
    _attempt++;
    WidgetsBinding.instance.removeObserver(this);
    _loadTimer?.cancel();
    for (final subscription in _subscriptions) {
      subscription.cancel();
    }
    _video
      ?..pause()
      ..removeAttribute('src')
      ..load();
    super.dispose();
  }

  void _createPlayer(Object element) {
    final host = element as web.HTMLDivElement;
    host.style
      ..position = 'relative'
      ..width = '100%'
      ..height = '100%'
      ..backgroundColor = '#EDF3ED';
    final video = web.HTMLVideoElement()
      ..id = 'sokoun-demo-video'
      ..preload = 'none'
      ..autoplay = false
      ..playsInline = true
      ..defaultMuted = true
      ..muted = true
      ..controls = true
      ..poster = _assetUrl(DemoVideoCard.posterAsset)
      ..src = _assetUrl(DemoVideoCard.videoAsset);
    video.setAttribute('aria-label', LocaleKeys.landingDemoVideoSemantic);
    video.style
      ..display = 'block'
      ..width = '100%'
      ..height = '100%'
      ..objectFit = 'contain'
      ..borderTopLeftRadius = '24px'
      ..borderTopRightRadius = '24px';
    final button = web.HTMLButtonElement()..type = 'button';
    button.style
      ..position = 'absolute'
      ..top = '50%'
      ..left = '50%'
      ..transform = 'translate(-50%, -50%)'
      ..padding = '12px 22px'
      ..border = '0'
      ..borderRadius = '40px'
      ..backgroundColor = '#0C6254'
      ..color = '#FFFFFF'
      ..font = '700 14px system-ui, sans-serif'
      ..whiteSpace = 'nowrap'
      ..cursor = 'pointer';
    host
      ..appendChild(video)
      ..appendChild(button);
    _video = video;
    _playButton = button;
    _subscriptions.addAll([
      button.onClick.listen((_) => _play()),
      video.onPlaying.listen((_) {
        _loadTimer?.cancel();
        _loading = false;
        _failed = false;
        widget.onFailureChanged(false);
        _updateButton();
      }),
      video.onPlay.listen((_) => _waitForPlayback(_attempt)),
      video.onWaiting.listen((_) {
        if (!video.paused) _waitForPlayback(_attempt);
      }),
      video.onPause.listen((_) {
        if (video.paused) _pause();
      }),
      video.onEnded.listen((_) => _updateButton()),
      video.onError.listen((_) {
        _fail('Media error ${video.error?.code}: ${video.error?.message}');
      }),
    ]);
    _updateButton();
  }

  void _play() {
    final video = _video;
    if (_disposed || video == null || _loading) return;
    final attempt = ++_attempt;
    if (_failed || video.error != null) {
      // A retry uses a fresh request instead of reusing a cached failed or
      // partial response. Native controls remain available during loading.
      video.src = Uri.parse(_assetUrl(DemoVideoCard.videoAsset))
          .replace(
            queryParameters: {
              'retry': DateTime.now().millisecondsSinceEpoch.toString(),
            },
          )
          .toString();
      video.load();
    }
    if (video.ended) video.currentTime = 0;
    _failed = false;
    _loading = true;
    // No awaits before this call: preserve the browser's trusted click/tap.
    final started = video.play().toDart;
    widget.onFailureChanged(false);
    _waitForPlayback(attempt);
    started.then(
      (_) {
        if (_disposed || attempt != _attempt) return;
        _loadTimer?.cancel();
        _loading = false;
        _updateButton();
      },
      onError: (Object error) {
        if (!_disposed && attempt == _attempt) _fail(error.toString());
      },
    );
  }

  void _waitForPlayback(int attempt) {
    if (_disposed || _loadTimer?.isActive == true) return;
    _loading = true;
    _updateButton();
    _loadTimer = Timer(const Duration(seconds: 20), () {
      if (!_disposed && attempt == _attempt && _loading) {
        _pause();
        _fail('Timed out waiting for playback.');
      }
    });
  }

  void _fail(String reason) {
    if (_disposed) return;
    _attempt++;
    _loadTimer?.cancel();
    _loading = false;
    _failed = true;
    debugPrint('Sokoun demo playback failed: $reason');
    widget.onFailureChanged(true);
    _updateButton();
  }

  void _updateButton() {
    final video = _video;
    final button = _playButton;
    if (_disposed || video == null || button == null) return;
    button.hidden = (!video.paused && !_loading && !_failed).toJS;
    button.disabled = _loading;
    final label = _loading
        ? LocaleKeys.landingDemoLoading
        : _failed
        ? LocaleKeys.landingDemoRetry
        : video.ended
        ? LocaleKeys.landingDemoReplay
        : LocaleKeys.landingDemoPlay;
    button
      ..textContent = '${_loading ? '' : '▶ '} $label'.trim()
      ..setAttribute('aria-label', label)
      ..setAttribute('aria-busy', _loading.toString());
  }

  void _createVideoLink(Object element) {
    final link = element as web.HTMLAnchorElement;
    link
      ..href = _assetUrl(DemoVideoCard.videoAsset)
      ..target = '_blank'
      ..rel = 'noopener'
      ..textContent = LocaleKeys.landingDemoOpen;
    link.style
      ..display = 'flex'
      ..alignItems = 'center'
      ..justifyContent = 'center'
      ..height = '100%'
      ..color = '#0C6254'
      ..font = '14px system-ui, sans-serif';
  }

  @override
  Widget build(BuildContext context) => Column(
    crossAxisAlignment: CrossAxisAlignment.stretch,
    children: [
      ClipRRect(
        borderRadius: const BorderRadius.vertical(top: Radius.circular(24)),
        child: AspectRatio(
          aspectRatio: 16 / 9,
          child: HtmlElementView.fromTagName(
            tagName: 'div',
            onElementCreated: _createPlayer,
          ),
        ),
      ),
      const Divider(height: 1, color: LandingColors.border),
      SizedBox(
        height: 44,
        child: HtmlElementView.fromTagName(
          tagName: 'a',
          onElementCreated: _createVideoLink,
        ),
      ),
    ],
  );
}
