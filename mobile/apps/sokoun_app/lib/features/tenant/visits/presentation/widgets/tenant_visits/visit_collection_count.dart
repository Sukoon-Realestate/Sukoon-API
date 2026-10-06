import 'package:flutter/material.dart';
import 'package:flutter_bloc/flutter_bloc.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';
import 'package:melos_core/config/language/locale_keys.g.dart';
import 'package:melos_core/config/res/config_imports.dart';
import 'package:melos_core/core/base_crud/code/presentation/cubit/base_cubit/async_cubit.dart';
import 'package:melos_core/core/helpers/text_style_manager.dart';
import 'package:melos_core/core/widgets/app_text.dart';
import 'package:sokoun_app/features/shared/unread_counts/data/models/unread_counts.dart';
import 'package:sokoun_app/features/shared/unread_counts/presentation/cubits/unread_counts_cubit.dart';

class VisitCollectionCount extends StatelessWidget {
  const VisitCollectionCount({super.key, this.initialCount});

  final int? initialCount;

  @override
  Widget build(BuildContext context) {
    final cubit = context.read<UnreadCountsCubit?>();
    if (initialCount != null) return _label(initialCount!);
    if (cubit == null) return const SizedBox.shrink();
    return BlocSelector<UnreadCountsCubit, AsyncState<UnreadCounts>, int>(
      bloc: cubit,
      selector: (state) => state.data.tenant.visits,
      builder: (context, count) => _label(count),
    );
  }

  Widget _label(int count) => Padding(
    padding: EdgeInsets.symmetric(horizontal: 20.w, vertical: 10.h),
    child: AppText(
      '$count ${LocaleKeys.tenantVisitsTitle}',
      style: AppTextStyles.regular12.copyWith(color: AppColors.sokoonGray),
    ),
  );
}
