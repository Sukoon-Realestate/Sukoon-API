part of '../../imports.dart';

class ProfileVerificationScreen extends StatefulWidget {
  const ProfileVerificationScreen({super.key, required this.workspace});
  final AppWorkspace workspace;
  @override
  State<ProfileVerificationScreen> createState() =>
      _ProfileVerificationScreenState();
}

class _ProfileVerificationScreenState extends State<ProfileVerificationScreen> {
  late final ProfileVerificationCubit _cubit;
  late final Future<void> _loadRequest;
  @override
  void initState() {
    super.initState();
    _cubit = ProfileVerificationCubit();
    _loadRequest = _cubit.load();
  }

  Future<void> _reload() async {
    await _loadRequest;
    if (mounted) await _cubit.load();
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
      title: LocaleKeys.profileIdentityVerification,
      actions: [
        IconButton(
          tooltip: LocaleKeys.supportRefresh,
          onPressed: _reload,
          icon: const Icon(Icons.refresh_rounded),
        ),
      ],
      body: SafeArea(
        child:
            StatusBuilder<
              ProfileVerificationCubit,
              ProfileVerificationContent
            >.withShimmer(
              initialDataForShimmer: const ProfileVerificationContent.initial(),
              onRetry: _reload,
              builder: (content) => ProfileVerificationContentView(
                content: content,
                workspace: widget.workspace,
              ),
            ),
      ),
    ),
  );
}
