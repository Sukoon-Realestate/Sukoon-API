part of '../../imports.dart';

class OwnerPropertyAnalyticsScreen extends StatefulWidget {
  const OwnerPropertyAnalyticsScreen({
    super.key,
    required this.property,
    this.analytics,
  });
  final OwnerPropertyContent property;
  final OwnerPropertyAnalyticsContent? analytics;
  @override
  State<OwnerPropertyAnalyticsScreen> createState() =>
      _OwnerPropertyAnalyticsScreenState();
}

class _OwnerPropertyAnalyticsScreenState
    extends State<OwnerPropertyAnalyticsScreen> {
  late final OwnerPropertyAnalyticsCubit _cubit;
  final ValueNotifier<String> _period = ValueNotifier('30_days');
  Future<void> _load() =>
      _cubit.load(propertyId: widget.property.id, period: _period.value);

  @override
  void initState() {
    super.initState();
    _cubit = OwnerPropertyAnalyticsCubit();
    if (widget.analytics == null) _load();
  }

  @override
  void dispose() {
    _cubit.close();
    _period.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) => BlocProvider.value(
    value: _cubit,
    child: AppScaffold(
      title: LocaleKeys.ownerAnalyticsTitle,
      showBackButton: true,
      backgroundColor: context.appColor(
        AppColors.scaffoldBackground,
        surface: true,
      ),
      contentWidth: SokounContentWidth.wide,
      body: SafeArea(
        child: Column(
          children: [
            if (widget.analytics == null)
              ValueListenableBuilder<String>(
                valueListenable: _period,
                builder: (context, period, _) => Padding(
                  padding: EdgeInsets.symmetric(
                    horizontal: 20.w,
                    vertical: 8.h,
                  ),
                  child: DropdownButtonFormField<String>(
                    isExpanded: true,
                    initialValue: period,
                    decoration: InputDecoration(
                      labelText: LocaleKeys.ownerAnalyticsPeriod,
                    ),
                    items: [
                      DropdownMenuItem(
                        value: '7_days',
                        child: AppText(LocaleKeys.ownerAnalyticsSevenDays),
                      ),
                      DropdownMenuItem(
                        value: '30_days',
                        child: AppText(LocaleKeys.ownerAnalyticsThirtyDays),
                      ),
                      DropdownMenuItem(
                        value: '90_days',
                        child: AppText(LocaleKeys.ownerAnalyticsNinetyDays),
                      ),
                    ],
                    onChanged: (value) {
                      if (value == null || value == _period.value) return;
                      _period.value = value;
                      _load();
                    },
                  ),
                ),
              ),
            Expanded(
              child: widget.analytics != null
                  ? OwnerAnalyticsContent(
                      propertyTitle: widget.property.title,
                      analytics: widget.analytics!,
                    )
                  : StatusBuilder<
                      OwnerPropertyAnalyticsCubit,
                      OwnerPropertyAnalyticsContent
                    >.withShimmer(
                      initialDataForShimmer:
                          const OwnerPropertyAnalyticsContent.initial(),
                      onRetry: _load,
                      shimmerBuilder: (_) => const SizedBox.expand(),
                      builder: (data) => OwnerAnalyticsContent(
                        propertyTitle: widget.property.title,
                        analytics: data,
                      ),
                    ),
            ),
          ],
        ),
      ),
    ),
  );
}
