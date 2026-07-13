import 'package:flutter/material.dart';
import 'package:melos_core/config/res/config_imports.dart';

import '../widgets/owner_add_property/imports.dart';

class OwnerAddPropertyFlowScreen extends StatefulWidget {
  const OwnerAddPropertyFlowScreen({super.key});

  @override
  State<OwnerAddPropertyFlowScreen> createState() =>
      _OwnerAddPropertyFlowScreenState();
}

class _OwnerAddPropertyFlowScreenState
    extends State<OwnerAddPropertyFlowScreen> {
  late final PageController _pageController;

  @override
  void initState() {
    super.initState();
    _pageController = PageController();
  }

  @override
  void dispose() {
    _pageController.dispose();
    super.dispose();
  }

  void _goToPage(int page) {
    _pageController.animateToPage(
      page,
      duration: const Duration(milliseconds: 280),
      curve: Curves.easeOutCubic,
    );
  }

  @override
  Widget build(BuildContext context) {
    return Directionality(
      textDirection: TextDirection.rtl,
      child: Scaffold(
        backgroundColor: AppColors.scaffoldBackground,
        body: SafeArea(
          child: PageView(
            controller: _pageController,
            physics: const NeverScrollableScrollPhysics(),
            children: [
              AddPropertyBasicsPage(onNext: () => _goToPage(1)),
              AddPropertyPhotosPage(
                onBack: () => _goToPage(0),
                onNext: () => _goToPage(2),
              ),
              AddPropertyPricingPage(
                onBack: () => _goToPage(1),
                onNext: () => _goToPage(3),
              ),
              AddPropertyExtraDetailsPage(
                onBack: () => _goToPage(2),
                onNext: () => _goToPage(4),
              ),
              AddPropertySubmittedPage(onAddAnother: () => _goToPage(0)),
            ],
          ),
        ),
      ),
    );
  }
}
