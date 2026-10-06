part of '../../imports.dart';

class OwnerRevenueScreen extends StatefulWidget {
  const OwnerRevenueScreen({super.key, this.showBackButton = true});
  final bool showBackButton;
  @override
  State<OwnerRevenueScreen> createState() => _OwnerRevenueScreenState();
}

class _OwnerRevenueScreenState extends State<OwnerRevenueScreen> {
  late final OwnerRevenueCubit _cubit;
  @override
  void initState() {
    super.initState();
    _cubit = OwnerRevenueCubit();
    _cubit.load();
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
      title: LocaleKeys.ownerRevenueTitle,
      showBackButton: widget.showBackButton,
      backgroundColor: context.appColor(
        AppColors.scaffoldBackground,
        surface: true,
      ),
      contentWidth: SokounContentWidth.wide,
      body: SafeArea(
        child:
            StatusBuilder<OwnerRevenueCubit, OwnerRevenueContent>.withShimmer(
              initialDataForShimmer: const OwnerRevenueContent.initial(),
              onRetry: _cubit.load,
              shimmerBuilder: (_) => const SizedBox.expand(),
              builder: (data) => OwnerRevenueContentView(data: data),
            ),
      ),
    ),
  );
}
