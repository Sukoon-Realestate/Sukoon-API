part of '../../imports.dart';

class LanguageSelectionScreen extends StatefulWidget {
  const LanguageSelectionScreen({super.key});

  @override
  State<LanguageSelectionScreen> createState() =>
      _LanguageSelectionScreenState();
}

class _LanguageSelectionScreenState extends State<LanguageSelectionScreen> {
  late final ValueNotifier<Languages> _selectedLanguage;
  bool _initialized = false;
  bool _isConfirming = false;

  @override
  void didChangeDependencies() {
    super.didChangeDependencies();
    if (!_initialized) {
      _selectedLanguage = ValueNotifier<Languages>(
        Languages.values.firstWhere(
          (language) => language.locale == context.locale,
          orElse: () => Languages.arabic,
        ),
      );
      _initialized = true;
    }
  }

  @override
  void dispose() {
    _selectedLanguage.dispose();
    super.dispose();
  }

  Future<void> _confirmLanguage(BuildContext context) async {
    if (_isConfirming) return;
    _isConfirming = true;
    final ModalRoute<dynamic>? route = ModalRoute.of(context);
    try {
      await context.setLocale(_selectedLanguage.value.locale);
      if (mounted && route?.isCurrent == true) Go.back();
    } finally {
      _isConfirming = false;
    }
  }

  @override
  Widget build(BuildContext context) {
    return AppScaffold(
      showBackButton: false,
      backgroundColor: AppColors.scaffoldBackground,
      body: SafeArea(
        child: Stack(
          fit: StackFit.expand,
          children: [
            LayoutBuilder(
              builder: (context, constraints) => SingleChildScrollView(
                child: ConstrainedBox(
                  constraints: BoxConstraints(minHeight: constraints.maxHeight),
                  child: Column(
                    mainAxisAlignment: MainAxisAlignment.center,
                    crossAxisAlignment: CrossAxisAlignment.stretch,
                    children: [
                      const LanguageSelectionHeader(),
                      32.szH,
                      ValueListenableBuilder<Languages>(
                        valueListenable: _selectedLanguage,
                        builder: (context, selectedLanguage, _) =>
                            LanguageSelectionOptions(
                              selectedLanguage: selectedLanguage,
                              onLanguageSelected: (language) =>
                                  _selectedLanguage.value = language,
                            ),
                      ),
                      32.szH,
                      DecoratedBox(
                        decoration: BoxDecoration(
                          borderRadius: BorderRadius.circular(12.r),
                          boxShadow: [
                            BoxShadow(
                              color: AppColors.tealAlpha19,
                              blurRadius: 16.r,
                              offset: Offset(0, 4.h),
                            ),
                          ],
                        ),
                        child: AppLoadingButton(
                          asyncCall: _confirmLanguage,
                          title: LocaleKeys.confirm,
                          buttonColor: AppColors.sokoonTeal,
                          borderRadius: 12.r,
                          height: 48.h,
                          textStyle: AppTextStyles.bold15.copyWith(
                            fontSize: 15.sp,
                            height: 1.45,
                          ),
                        ),
                      ),
                    ],
                  ).paddingSymmetric(horizontal: 24.w, vertical: 64.h),
                ),
              ),
            ),
            PositionedDirectional(
              top: 12.h,
              start: 16.w,
              child: IconButton(
                onPressed: () => Go.back(),
                tooltip: MaterialLocalizations.of(context).backButtonTooltip,
                icon: Icon(
                  Icons.arrow_back_rounded,
                  color: AppColors.sokoonNavy,
                  size: 22.r,
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }
}
