import 'package:flutter/material.dart';
import 'package:flutter/rendering.dart';

import '../models/landing_content.dart';
import '../widgets/imports.dart';

class LandingPage extends StatefulWidget {
  const LandingPage({super.key});

  @override
  State<LandingPage> createState() => _LandingPageState();
}

class _LandingPageState extends State<LandingPage> {
  final _scrollController = ScrollController();
  final _sectionKeys = <String, GlobalKey>{
    'hero': GlobalKey(),
    'audience': GlobalKey(),
    'how': GlobalKey(),
    'properties': GlobalKey(),
    'trust': GlobalKey(),
    'faq': GlobalKey(),
    'download': GlobalKey(),
    'app': GlobalKey(),
  };

  var _audience = Audience.tenant;
  var _scrolled = false;

  @override
  void initState() {
    super.initState();
    _scrollController.addListener(_handleScroll);
  }

  @override
  void dispose() {
    _scrollController
      ..removeListener(_handleScroll)
      ..dispose();
    super.dispose();
  }

  void _handleScroll() {
    final nextScrolled = _scrollController.offset > 60;
    if (nextScrolled != _scrolled) {
      setState(() => _scrolled = nextScrolled);
    }
  }

  Future<void> _navigateTo(String section) async {
    var target = section;
    if (section == 'tenant' || section == 'owner') {
      final nextAudience = section == 'tenant'
          ? Audience.tenant
          : Audience.owner;
      if (_audience != nextAudience) {
        setState(() => _audience = nextAudience);
        await WidgetsBinding.instance.endOfFrame;
      }
      target = 'audience';
    }

    if (!mounted || !_scrollController.hasClients) return;
    final targetContext = _sectionKeys[target]?.currentContext;
    final renderObject = targetContext?.findRenderObject();
    if (renderObject == null || !renderObject.attached) return;

    final viewport = RenderAbstractViewport.maybeOf(renderObject);
    if (viewport == null) return;
    final revealOffset =
        viewport.getOffsetToReveal(renderObject, 0).offset - 68;
    final targetOffset = revealOffset.clamp(
      _scrollController.position.minScrollExtent,
      _scrollController.position.maxScrollExtent,
    );
    if (MediaQuery.disableAnimationsOf(context)) {
      _scrollController.jumpTo(targetOffset);
      return;
    }
    await _scrollController.animateTo(
      targetOffset,
      duration: const Duration(milliseconds: 650),
      curve: Curves.easeInOutCubic,
    );
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: SelectionArea(
        child: Scrollbar(
          controller: _scrollController,
          child: CustomScrollView(
            controller: _scrollController,
            physics: const ClampingScrollPhysics(),
            slivers: [
              SliverPersistentHeader(
                pinned: true,
                delegate: _HeaderDelegate(
                  scrolled: _scrolled,
                  onNavigate: _navigateTo,
                ),
              ),
              SliverToBoxAdapter(
                child: KeyedSubtree(
                  key: _sectionKeys['hero'],
                  child: HeroSection(onNavigate: _navigateTo),
                ),
              ),
              const SliverToBoxAdapter(child: TrustStrip()),
              SliverToBoxAdapter(
                child: KeyedSubtree(
                  key: _sectionKeys['audience'],
                  child: AudienceFeaturesSection(
                    audience: _audience,
                    onAudienceChanged: (value) {
                      setState(() => _audience = value);
                    },
                    onCtaPressed: () => _navigateTo('download'),
                  ),
                ),
              ),
              SliverToBoxAdapter(
                child: KeyedSubtree(
                  key: _sectionKeys['how'],
                  child: HowItWorksSection(
                    audience: _audience,
                    onAudienceChanged: (value) =>
                        setState(() => _audience = value),
                  ),
                ),
              ),
              SliverToBoxAdapter(
                child: KeyedSubtree(
                  key: _sectionKeys['properties'],
                  child: PropertyShowcaseSection(
                    onExplore: () => _navigateTo('app'),
                  ),
                ),
              ),
              SliverToBoxAdapter(
                child: KeyedSubtree(
                  key: _sectionKeys['trust'],
                  child: const PrivacyTrustSection(),
                ),
              ),
              SliverToBoxAdapter(
                child: KeyedSubtree(
                  key: _sectionKeys['app'],
                  child: const AppShowcaseSection(),
                ),
              ),
              SliverToBoxAdapter(
                child: KeyedSubtree(
                  key: _sectionKeys['download'],
                  child: FinalCtaSection(onNavigate: _navigateTo),
                ),
              ),
              SliverToBoxAdapter(
                child: KeyedSubtree(
                  key: _sectionKeys['faq'],
                  child: const FaqSection(),
                ),
              ),
              SliverToBoxAdapter(child: SiteFooter(onNavigate: _navigateTo)),
            ],
          ),
        ),
      ),
    );
  }
}

class _HeaderDelegate extends SliverPersistentHeaderDelegate {
  const _HeaderDelegate({required this.scrolled, required this.onNavigate});

  final bool scrolled;
  final ValueChanged<String> onNavigate;

  @override
  double get minExtent => 68;

  @override
  double get maxExtent => 68;

  @override
  Widget build(
    BuildContext context,
    double shrinkOffset,
    bool overlapsContent,
  ) {
    return SiteHeader(
      scrolled: scrolled || overlapsContent,
      onNavigate: onNavigate,
    );
  }

  @override
  bool shouldRebuild(covariant _HeaderDelegate oldDelegate) {
    return oldDelegate.scrolled != scrolled ||
        oldDelegate.onNavigate != onNavigate;
  }
}
