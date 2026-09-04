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
  late final Future<void> _ownerDashboardRequest;

  @override
  void initState() {
    super.initState();
    _ownerDashboardCubit = OwnerDashboardCubit();
    _ownerDashboardRequest = _ownerDashboardCubit.getDashboard();
  }

  @override
  void dispose() {
    _ownerDashboardCubit.close();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Directionality(
      textDirection: TextDirection.rtl,
      child: BlocProvider.value(
        value: _ownerDashboardCubit,
        child: Scaffold(
          backgroundColor: AppColors.scaffoldBackground,
          body: SafeArea(
            child:
                StatusBuilder<
                  OwnerDashboardCubit,
                  OwnerDashboardModel
                >.withShimmer(
                  initialDataForShimmer: const OwnerDashboardModel.initial(),
                  requestToTryAgainWhenError: _ownerDashboardRequest,
                  errorType: ErrorType.defaultView,
                  builder: (dashboard) =>
                      OwnerDashboardContent(dashboard: dashboard),
                ),
          ),
        ),
      ),
    );
  }
}
