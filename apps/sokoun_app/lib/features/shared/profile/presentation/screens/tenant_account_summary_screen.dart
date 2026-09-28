part of '../../imports.dart';

class TenantAccountSummaryScreen extends StatefulWidget {
  const TenantAccountSummaryScreen({super.key});

  @override
  State<TenantAccountSummaryScreen> createState() =>
      _TenantAccountSummaryScreenState();
}

class _TenantAccountSummaryScreenState
    extends State<TenantAccountSummaryScreen> {
  late final TenantAccountSummaryCubit _summaryCubit;
  late final Future<void> _summaryRequest;

  @override
  void initState() {
    super.initState();
    _summaryCubit = TenantAccountSummaryCubit();
    _summaryRequest = _summaryCubit.getSummary();
  }

  @override
  void dispose() {
    _summaryCubit.close();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return BlocProvider<TenantAccountSummaryCubit>.value(
      value: _summaryCubit,
      child: Scaffold(
        backgroundColor: AppColors.scaffoldBackground,
        body: SafeArea(
          child: Column(
            children: [
              ProfileScreenHeader(
                title: LocaleKeys.profileSummaryTitle,
                showBackButton: true,
              ),
              Expanded(
                child:
                    StatusBuilder<
                      TenantAccountSummaryCubit,
                      TenantAccountSummaryContent
                    >.withShimmer(
                      initialDataForShimmer:
                          const TenantAccountSummaryContent.initial(),
                      requestToTryAgainWhenError: _summaryRequest,
                      onRetry: _summaryCubit.getSummary,
                      errorType: ErrorType.defaultView,
                      builder: (summary) =>
                          TenantAccountSummaryContentView(summary: summary),
                    ),
              ),
            ],
          ),
        ),
      ),
    );
  }
}
