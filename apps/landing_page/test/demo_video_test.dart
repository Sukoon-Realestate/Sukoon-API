import 'dart:async';
import 'dart:convert';
import 'dart:io';

// ignore: implementation_imports
import 'package:easy_localization/src/localization.dart';
// ignore: implementation_imports
import 'package:easy_localization/src/translations.dart';
import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:landing_page/landing/theme/landing_theme.dart';
import 'package:landing_page/landing/widgets/app_showcase/demo_video_card.dart';
import 'package:video_player_platform_interface/video_player_platform_interface.dart';

void main() {
  TestWidgetsFlutterBinding.ensureInitialized();
  late _DemoVideoPlatform platform;
  late VideoPlayerPlatform originalPlatform;

  setUp(() {
    Localization.load(
      const Locale('en'),
      translations: Translations(
        jsonDecode(
              File(
                '../../packages/core/assets/translations/en.json',
              ).readAsStringSync(),
            )
            as Map<String, dynamic>,
      ),
    );
    originalPlatform = VideoPlayerPlatform.instance;
    platform = _DemoVideoPlatform();
    VideoPlayerPlatform.instance = platform;
  });
  tearDown(() => VideoPlayerPlatform.instance = originalPlatform);

  Future<void> mount(WidgetTester tester) async {
    tester.view.physicalSize = const Size(800, 900);
    tester.view.devicePixelRatio = 1;
    addTearDown(tester.view.reset);
    await tester.pumpWidget(
      MaterialApp(
        theme: LandingTheme.theme,
        home: const Scaffold(
          body: SingleChildScrollView(child: DemoVideoCard()),
        ),
      ),
    );
    await tester.pumpAndSettle();
  }

  Future<void> play(WidgetTester tester) async {
    await tester.tap(find.text('Play demo'));
    await tester.pump();
    await tester.pump(const Duration(milliseconds: 10));
  }

  testWidgets('shows a poster and transcript without loading the video', (
    tester,
  ) async {
    await mount(tester);
    expect(platform.sources, isEmpty);
    expect(find.text('Play demo'), findsOneWidget);
    expect(
      tester.widget<Image>(find.byType(Image)).image,
      const AssetImage(DemoVideoCard.posterAsset),
    );
    await tester.tap(find.text('Read the walkthrough'));
    await tester.pumpAndSettle();
    expect(
      find.textContaining('Choose a day and an available time'),
      findsOneWidget,
    );
    expect(platform.sources, isEmpty);
  });

  testWidgets(
    'loads the bundled asset on play and supports pause and seeking',
    (tester) async {
      await mount(tester);
      await play(tester);
      expect(platform.sources.single.sourceType, DataSourceType.asset);
      expect(platform.sources.single.asset, DemoVideoCard.videoAsset);
      expect(platform.playCalls, 1);
      expect(find.byTooltip('Pause demo'), findsOneWidget);
      tester.widget<Slider>(find.byType(Slider)).onChanged!(15000);
      await tester.pump();
      expect(platform.position, const Duration(seconds: 15));
      final pausesBefore = platform.pauseCalls;
      await tester.tap(find.byTooltip('Pause demo'));
      await tester.pump();
      expect(platform.pauseCalls, pausesBefore + 1);
      expect(find.text('Play demo'), findsOneWidget);
      await tester.pumpWidget(const SizedBox.shrink());
      await tester.pumpAndSettle();
      await tester.runAsync(() => Future<void>.delayed(Duration.zero));
      expect(platform.disposed, 1);
    },
  );

  testWidgets('pauses when the app goes into the background', (tester) async {
    await mount(tester);
    await play(tester);
    tester.binding.handleAppLifecycleStateChanged(AppLifecycleState.paused);
    await tester.pump();
    expect(platform.pauseCalls, greaterThanOrEqualTo(1));
    tester.binding.handleAppLifecycleStateChanged(AppLifecycleState.resumed);
    await tester.pump();
    expect(find.text('Play demo'), findsOneWidget);
    expect(platform.playCalls, 1);
    await tester.pumpWidget(const SizedBox.shrink());
    await tester.pump();
  });

  testWidgets(
    'offers retry after a playback error and releases the old player',
    (tester) async {
      await mount(tester);
      await play(tester);
      platform.streams[1]!.addError(
        PlatformException(
          code: 'demo-load-failed',
          message: 'The test video failed to load',
        ),
      );
      await tester.pump();
      await tester.pump();
      expect(find.textContaining('The video could not load.'), findsOneWidget);
      await tester.tap(find.text('Try playing again'));
      await tester.runAsync(() => Future<void>.delayed(Duration.zero));
      await tester.pump();
      await tester.pump(const Duration(milliseconds: 10));
      expect(platform.sources, hasLength(2));
      expect(platform.disposed, 1);
      expect(find.byTooltip('Pause demo'), findsOneWidget);
      await tester.pumpWidget(const SizedBox.shrink());
      await tester.pump();
    },
  );

  testWidgets('replays from the start after reaching the end', (tester) async {
    await mount(tester);
    await play(tester);
    platform.streams[1]!.add(VideoEvent(eventType: VideoEventType.completed));
    await tester.pump();
    await tester.pump(const Duration(milliseconds: 10));
    expect(find.text('Replay demo'), findsOneWidget);
    await tester.tap(find.text('Replay demo'));
    await tester.pump();
    expect(platform.position, Duration.zero);
    expect(platform.playCalls, 2);
    await tester.pumpWidget(const SizedBox.shrink());
    await tester.pump();
  });
}

class _DemoVideoPlatform extends VideoPlayerPlatform {
  final sources = <DataSource>[];
  final streams = <int, StreamController<VideoEvent>>{};
  int playCalls = 0;
  int pauseCalls = 0;
  int disposed = 0;
  Duration position = Duration.zero;

  @override
  Future<void> init() async {}

  @override
  Future<int?> createWithOptions(VideoCreationOptions options) async {
    sources.add(options.dataSource);
    final id = sources.length;
    final stream = StreamController<VideoEvent>();
    streams[id] = stream;
    stream.add(
      VideoEvent(
        eventType: VideoEventType.initialized,
        duration: const Duration(seconds: 40),
        size: const Size(1280, 720),
      ),
    );
    return id;
  }

  @override
  Stream<VideoEvent> videoEventsFor(int playerId) => streams[playerId]!.stream;
  @override
  Future<void> dispose(int playerId) async {
    disposed++;
    await streams.remove(playerId)?.close();
  }

  @override
  Future<void> play(int playerId) async => playCalls++;
  @override
  Future<void> pause(int playerId) async => pauseCalls++;
  @override
  Future<void> seekTo(int playerId, Duration value) async => position = value;
  @override
  Future<Duration> getPosition(int playerId) async => position;
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
