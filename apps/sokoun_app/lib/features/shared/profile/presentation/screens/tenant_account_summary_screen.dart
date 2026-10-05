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

  @override
  void initState() {
    super.initState();
    _summaryCubit = TenantAccountSummaryCubit();
    _summaryCubit.getSummary();
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
      child: AppScaffold(
        title: LocaleKeys.profileSummaryTitle,
        showBackButton: true,
        backgroundColor: context.appColor(
          AppColors.scaffoldBackground,
          surface: true,
        ),
        body: SafeArea(
          child:
              StatusBuilder<
                    TenantAccountSummaryCubit,
                    TenantAccountSummaryContent
                  >.withShimmer(
                    initialDataForShimmer:
                        const TenantAccountSummaryContent.initial(),
                    onRetry: _summaryCubit.getSummary,
                    errorType: ErrorType.defaultView,
                    builder: (summary) =>
                        TenantAccountSummaryContentView(summary: summary),
                  )
                  .withPullRefresher(onRefresh: _summaryCubit.getSummary),
        ),
      ),
    );
  }
}
