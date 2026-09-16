import 'package:flutter/material.dart';
import 'package:flutter_bloc/flutter_bloc.dart';
import 'package:melos_core/config/res/config_imports.dart';
import 'package:melos_core/core/helpers/status_builder.dart';
import 'package:sokoun_app/features/tenant/home/data/models/home_page_model.dart';
import 'package:sokoun_app/features/tenant/home/presentation/cubits/home_page_cubit.dart';

import '../widgets/tenant_widgets/imports.dart';

class TenantHomeScreen extends StatefulWidget {
  const TenantHomeScreen({super.key});

  @override
  State<TenantHomeScreen> createState() => _TenantHomeScreenState();
}

class _TenantHomeScreenState extends State<TenantHomeScreen> {
  late final HomePageCubit _homePageCubit;
  late final Future<void> _homePageRequest;

  @override
  void initState() {
    super.initState();
    _homePageCubit = HomePageCubit();
    _homePageRequest = _homePageCubit.getHomePage();
  }

  @override
  void dispose() {
    _homePageCubit.close();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: AppColors.scaffoldBackground,
      body: SafeArea(
        child: BlocProvider<HomePageCubit>.value(
          value: _homePageCubit,
          child: StatusBuilder<HomePageCubit, HomePageModel>.withShimmer(
            initialDataForShimmer: const HomePageModel.initial(),
            requestToTryAgainWhenError: _homePageRequest,
            errorType: ErrorType.defaultView,
            builder: (data) => TenantHomeContent(
              properties: data.results,
              showVisitBanner: data.banner != null,
            ),
          ),
        ),
      ),
    );
  }
}
