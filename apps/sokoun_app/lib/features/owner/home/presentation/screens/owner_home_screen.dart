import 'package:melos_core/core/base_crud/code/presentation/cubit/base_cubit/async_cubit.dart';
import 'package:sokoun_app/shared_widgets/sokoun_layout.dart';
import 'package:sokoun_app/shared_widgets/app_scaffold.dart';
import 'package:flutter/material.dart';
import 'package:flutter_bloc/flutter_bloc.dart';
import 'package:melos_core/config/res/config_imports.dart';
import 'package:melos_core/core/helpers/status_builder.dart';
import 'package:sokoun_app/features/owner/home/data/models/owner_dashboard_model.dart';
import 'package:sokoun_app/features/owner/home/presentation/cubits/owner_dashboard_cubit.dart';

import '../widgets/owner_widgets/imports.dart';

class OwnerHomeScreen extends StatefulWidget {
  const OwnerHomeScreen({super.key});

  @override
  State<OwnerHomeScreen> createState() => _OwnerHomeScreenState();
}

class _OwnerHomeScreenState extends State<OwnerHomeScreen> {
  late final OwnerDashboardCubit _ownerDashboardCubit;
  late Future<void> _ownerDashboardRequest;

  @override
  void initState() {
    super.initState();
    _ownerDashboardCubit = OwnerDashboardCubit();
    _ownerDashboardRequest = _ownerDashboardCubit.getDashboard();
  }

  Future<void> _refreshDashboard() async {
    final Future<void> request = _ownerDashboardCubit.getDashboard();
    _ownerDashboardRequest = request;
    await request;
  }

  @override
  void dispose() {
    _ownerDashboardCubit.close();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return BlocProvider.value(
      value: _ownerDashboardCubit,
      child: AppScaffold(
        titleWidget:
            BlocBuilder<OwnerDashboardCubit, AsyncState<OwnerDashboardModel>>(
              builder: (context, state) => OwnerHomeAppBarTitle(
                avatarUrl: state.data.owner.avatar,
                isVerified: state.data.owner.isVerified,
              ),
            ),
        showBackButton: false,
        toolbarHeight: 96 + MediaQuery.textScalerOf(context).scale(38),
        backgroundColor: AppColors.scaffoldBackground,
        contentWidth: SokounContentWidth.wide,
        body: SafeArea(
          child:
              StatusBuilder<
                OwnerDashboardCubit,
                OwnerDashboardModel
              >.withShimmer(
                initialDataForShimmer: const OwnerDashboardModel.initial(),
                requestToTryAgainWhenError: _ownerDashboardRequest,
                onRetry: _refreshDashboard,
                builder: (dashboard) => OwnerDashboardContent(
                  dashboard: dashboard,
                  onRequestResolved: _refreshDashboard,
                ),
              ),
        ),
      ),
    );
  }
}
