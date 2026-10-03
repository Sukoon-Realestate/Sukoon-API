part of '../../imports.dart';

class SupportScreen extends StatefulWidget {
  const SupportScreen({super.key, required this.workspace});
  final AppWorkspace workspace;
  @override
  State<SupportScreen> createState() => _SupportScreenState();
}

class _SupportScreenState extends State<SupportScreen> {
  late final SupportHelpCubit _cubit;
  late final Future<void> _loadRequest;
  late final String _language;
  @override
  void initState() {
    super.initState();
    _cubit = SupportHelpCubit();
    _language = Languages.currentLanguage.locale.languageCode;
    _loadRequest = _load();
  }

  Future<void> _load() =>
      _cubit.load(workspace: widget.workspace, language: _language);
  Future<void> _retry() async {
    await _loadRequest;
    if (mounted) await _load();
  }

  @override
  void dispose() {
    _cubit.close();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) => BlocProvider.value(
    value: _cubit,
    child: AppScaffold(
      title: widget.workspace.isOwner
          ? LocaleKeys.supportOwnerTitle
          : LocaleKeys.profileHelpCenter,
      body: SafeArea(
        child: ListView(
          children: [
            SupportHelpHeader(workspace: widget.workspace),
            StatusBuilder<SupportHelpCubit, SupportHelpContent>.withShimmer(
              initialDataForShimmer: const SupportHelpContent.initial(),
              onRetry: _retry,
              builder: (content) => SupportHelpContentView(content: content),
            ),
          ],
        ),
      ),
    ),
  );
}
