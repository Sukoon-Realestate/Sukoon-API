import 'dart:async';
import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:melos_core/config/language/locale_keys.g.dart';
import 'package:melos_core/core/navigation/navigator.dart';
import 'package:melos_core/core/shared/route_observer.dart';
import 'package:sokoun_app/features/tenant/home/presentation/widgets/tenant_property_details/property_video.dart';
import 'package:video_player_platform_interface/video_player_platform_interface.dart';

void main() {
  TestWidgetsFlutterBinding.ensureInitialized();
  late _VideoPlatform platform;
  late VideoPlayerPlatform original;
  setUp(() {
    original = VideoPlayerPlatform.instance;
    platform = _VideoPlatform();
    VideoPlayerPlatform.instance = platform;
  });
  tearDown(() {
    VideoPlayerPlatform.instance = original;
  });

  Widget app() => ScreenUtilInit(
    designSize: const Size(360, 690),
    builder: (_, __) => MaterialApp(
      navigatorKey: Go.navigatorKey,
      navigatorObservers: [AppNavigationObserver.instance],
      home: const Scaffold(
        body: PropertyVideo(
          url: 'https://cdn.example.com/tour.mp4',
          durationSeconds: 45,
        ),
      ),
    ),
  );

  testWidgets('video starts on tap, pauses under another route, and disposes', (
    tester,
  ) async {
    await tester.pumpWidget(app());
    await tester.pumpAndSettle();
    expect(platform.created, 0);
    expect(find.text('0:45'), findsOneWidget);
    await tester.tap(find.byTooltip(LocaleKeys.propertyVideoPlay));
    await tester.pumpAndSettle();
    expect(platform.created, 1);
    expect(platform.playing, isTrue);
    unawaited(Go.to(const Scaffold(body: Text('Other route'))));
    await tester.pumpAndSettle();
    expect(platform.playing, isFalse);
    await tester.pumpWidget(const SizedBox.shrink());
    await tester.runAsync(() async {
      await Future<void>.delayed(Duration.zero);
    });
    await tester.pumpAndSettle();
    await tester.pump(const Duration(milliseconds: 500));
    expect(platform.disposed, 1);
    expect(tester.takeException(), isNull);
  });

  testWidgets('video initialization failure offers a working retry', (
    tester,
  ) async {
    platform.fail = true;
    await tester.pumpWidget(app());
    await tester.pumpAndSettle();
    await tester.tap(find.byTooltip(LocaleKeys.propertyVideoPlay));
    await tester.pumpAndSettle();
    expect(find.text(LocaleKeys.propertyVideoError), findsOneWidget);
    platform.fail = false;
    await tester.tap(find.byTooltip(LocaleKeys.propertyVideoError));
    await tester.runAsync(() async {
      await Future<void>.delayed(Duration.zero);
    });
    await tester.pumpAndSettle();
    expect(platform.created, 2);
    expect(platform.disposed, 1);
    expect(platform.playing, isTrue);
    await tester.pumpWidget(const SizedBox.shrink());
    await tester.pumpAndSettle();
    expect(tester.takeException(), isNull);
  });

  testWidgets('backgrounding pauses playback and resuming does not autoplay', (
    tester,
  ) async {
    await tester.pumpWidget(app());
    await tester.pumpAndSettle();
    await tester.tap(find.byTooltip(LocaleKeys.propertyVideoPlay));
    await tester.pumpAndSettle();
    expect(platform.playing, isTrue);
    tester.binding.handleAppLifecycleStateChanged(AppLifecycleState.paused);
    await tester.pumpAndSettle();
    expect(platform.playing, isFalse);
    tester.binding.handleAppLifecycleStateChanged(AppLifecycleState.resumed);
    await tester.pumpAndSettle();
    expect(platform.playing, isFalse);
    await tester.pumpWidget(const SizedBox.shrink());
    await tester.pumpAndSettle();
  });

  testWidgets(
    'platform playback failure is recoverable without an uncaught error',
    (tester) async {
      await tester.pumpWidget(app());
      await tester.pumpAndSettle();
      await tester.tap(find.byTooltip(LocaleKeys.propertyVideoPlay));
      await tester.pumpAndSettle();
      await tester.tap(find.byTooltip(LocaleKeys.propertyVideoPause));
      await tester.pumpAndSettle();
      platform.failPlay = true;
      await tester.tap(find.byTooltip(LocaleKeys.propertyVideoPlay));
      await tester.pumpAndSettle();
      expect(find.text(LocaleKeys.propertyVideoError), findsOneWidget);
      expect(tester.takeException(), isNull);
      platform.failPlay = false;
      await tester.tap(find.byTooltip(LocaleKeys.propertyVideoError));
      await tester.runAsync(() async {
        await Future<void>.delayed(Duration.zero);
      });
      await tester.pumpAndSettle();
      expect(platform.created, 2);
      expect(platform.playing, isTrue);
      await tester.pumpWidget(const SizedBox.shrink());
      await tester.pumpAndSettle();
    },
  );
}

class _VideoPlatform extends VideoPlayerPlatform {
  int created = 0;
  int disposed = 0;
  bool playing = false;
  bool fail = false;
  bool failPlay = false;
  final Map<int, StreamController<VideoEvent>> streams = {};
  @override
  Future<void> init() async {}
  @override
  Future<int?> createWithOptions(VideoCreationOptions options) async {
    final id = ++created;
    final stream = StreamController<VideoEvent>();
    streams[id] = stream;
    if (fail) {
      stream.addError(
        PlatformException(code: 'VideoError', message: 'Cannot load video'),
      );
    } else {
      stream.add(
        VideoEvent(
          eventType: VideoEventType.initialized,
          size: const Size(640, 360),
          duration: const Duration(seconds: 45),
        ),
      );
    }
    return id;
  }

  @override
  Stream<VideoEvent> videoEventsFor(int playerId) => streams[playerId]!.stream;
  @override
  Future<void> dispose(int playerId) async {
    disposed++;
    await streams[playerId]?.close();
  }

  @override
  Future<void> play(int playerId) async {
    if (failPlay) {
      throw PlatformException(code: 'PlaybackError', message: 'Cannot play');
    }
    playing = true;
  }

  @override
  Future<void> pause(int playerId) async {
    playing = false;
  }

  @override
  Future<void> seekTo(int playerId, Duration position) async {}
  @override
  Future<Duration> getPosition(int playerId) async => Duration.zero;
  @override
  Future<void> setLooping(int playerId, bool looping) async {}
  @override
  Future<void> setVolume(int playerId, double volume) async {}
  @override
  Future<void> setPlaybackSpeed(int playerId, double speed) async {}
  @override
  Future<void> setMixWithOthers(bool mixWithOthers) async {}
  @override
  Widget buildView(int playerId) => const SizedBox.expand();
}
