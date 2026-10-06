import 'package:flutter/material.dart';
import 'package:flutter_bloc/flutter_bloc.dart';
import 'package:melos_core/core/base_crud/code/presentation/cubit/base_cubit/async_cubit.dart';
import 'package:melos_core/core/helpers/status_builder.dart';

class PremiumRemoteView<C extends AsyncCubit<T>, T> extends StatelessWidget {
  const PremiumRemoteView({
    super.key,
    required this.cubit,
    required this.request,
    required this.initialData,
    required this.onRetry,
    required this.builder,
  });
  final C cubit;
  final Future<void> request;
  final T initialData;
  final Future<void> Function() onRetry;
  final Widget Function(T) builder;
  @override
  Widget build(BuildContext context) => BlocProvider<C>.value(
    value: cubit,
    child: FutureBuilder<void>(
      future: request,
      builder: (context, snapshot) => StatusBuilder<C, T>.withShimmer(
        initialDataForShimmer: initialData,
        onRetry: onRetry,
        shimmerBuilder: (_) => const SizedBox(height: 200),
        builder: builder,
      ),
    ),
  );
}
