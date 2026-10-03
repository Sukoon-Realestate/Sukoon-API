part of '../../imports.dart';

class SupportTicketDetailScreen extends StatefulWidget {
  const SupportTicketDetailScreen({
    super.key,
    required this.id,
    required this.workspace,
  });
  final String id;
  final AppWorkspace workspace;
  @override
  State<SupportTicketDetailScreen> createState() =>
      _SupportTicketDetailScreenState();
}

class _SupportTicketDetailScreenState extends State<SupportTicketDetailScreen> {
  late final SupportTicketCubit _cubit;
  late final SupportReplyCubit _replyCubit;
  late final Future<void> _loadRequest;
  @override
  void initState() {
    super.initState();
    _cubit = SupportTicketCubit();
    _replyCubit = SupportReplyCubit();
    _loadRequest = _load();
  }

  Future<void> _load() =>
      _cubit.load(id: widget.id, workspace: widget.workspace);
  Future<void> _retry() async {
    await _loadRequest;
    if (mounted) await _load();
  }

  @override
  void dispose() {
    _cubit.close();
    _replyCubit.close();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) => MultiBlocProvider(
    providers: [
      BlocProvider.value(value: _cubit),
      BlocProvider.value(value: _replyCubit),
    ],
    child: AppScaffold(
      title: LocaleKeys.supportTicketDetails,
      actions: [
        BlocBuilder<SupportReplyCubit, AsyncState<SupportTicketContent>>(
          builder: (context, state) => IconButton(
            tooltip: LocaleKeys.supportRefresh,
            icon: const Icon(Icons.refresh_rounded),
            onPressed: state.isLoading ? null : _retry,
          ),
        ),
      ],
      body: SafeArea(
        child: SupportTicketDetailContentView(
          id: widget.id,
          workspace: widget.workspace,
          onRetry: _retry,
        ),
      ),
    ),
  );
}
