import 'dart:async';

import 'package:flutter/material.dart';
import 'package:flutter_bloc/flutter_bloc.dart';
import 'package:melos_core/config/res/config_imports.dart';
import 'package:melos_core/core/base_crud/code/presentation/cubit/base_cubit/async_cubit.dart';
import 'package:melos_core/core/helpers/status_builder.dart';
import 'package:melos_core/core/widgets/toast_messages/custom_messages.dart';
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
  late final ScrollController _scrollController;

  @override
  void initState() {
    super.initState();
    _homePageCubit = HomePageCubit();
    _scrollController = ScrollController()..addListener(_onScroll);
    _homePageRequest = _homePageCubit.getHomePage();
  }

  void _onScroll() {
    if (_scrollController.hasClients &&
        _scrollController.position.extentAfter <= 200 &&
        _homePageCubit.canLoadMore) {
      unawaited(_homePageCubit.loadMoreHomePage());
    }
  }

  @override
  void dispose() {
    _scrollController.dispose();
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
          child: BlocListener<HomePageCubit, AsyncState<HomePageModel>>(
            listenWhen: (previous, current) =>
                previous.isLoadingMore &&
                current.isSuccess &&
                (current.msg?.isNotEmpty ?? false),
            listener: (context, state) =>
                MessageUtils.showSnackBar(state.msg!, context: context),
            child: RefreshIndicator(
              onRefresh: _homePageCubit.getHomePage,
              child: StatusBuilder<HomePageCubit, HomePageModel>.withShimmer(
                initialDataForShimmer: const HomePageModel.initial(),
                requestToTryAgainWhenError: _homePageRequest,
                onRetry: _homePageCubit.getHomePage,
                errorType: ErrorType.defaultView,
                builder: (data) => TenantHomeContent(
                  properties: data.results,
                  showVisitBanner: data.banner != null,
                  scrollController: _scrollController,
                  isLoadingMore: _homePageCubit.state.isLoadingMore,
                ),
              ),
            ),
          ),
        ),
      ),
    );
  }
}
