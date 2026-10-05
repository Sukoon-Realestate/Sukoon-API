part of '../../../imports.dart';

class OwnerPropertyDeleteSheet extends StatefulWidget {
  const OwnerPropertyDeleteSheet({super.key, required this.property});

  final OwnerPropertyContent property;

  @override
  State<OwnerPropertyDeleteSheet> createState() =>
      _OwnerPropertyDeleteSheetState();
}

class _OwnerPropertyDeleteSheetState extends State<OwnerPropertyDeleteSheet> {
  late final DeleteOwnerPropertyCubit _cubit;

  @override
  void initState() {
    super.initState();
    _cubit = DeleteOwnerPropertyCubit();
  }

  @override
  void dispose() {
    _cubit.close();
    super.dispose();
  }

  Future<void> _deleteProperty() => _cubit.delete(
    propertyId: widget.property.id,
    onSuccess: () {
      if (mounted) Go.back(true);
    },
  );

  @override
  Widget build(BuildContext context) =>
      BlocBuilder<
        DeleteOwnerPropertyCubit,
        AsyncState<OwnerPropertyDeletionModel>
      >(
        bloc: _cubit,
        builder: (context, state) => PopScope(
          canPop: !state.isLoading,
          child: SafeArea(
            child: SingleChildScrollView(
              padding: EdgeInsets.all(24.w),
              child: Column(
                mainAxisSize: MainAxisSize.min,
                crossAxisAlignment: CrossAxisAlignment.stretch,
                spacing: 16.h,
                children: [
                  Icon(
                    Icons.delete_outline_rounded,
                    color: AppColors.red,
                    size: 44.r,
                  ),
                  AppText(
                    LocaleKeys.ownerPropertiesDeleteProperty,
                    style: AppTextStyles.bold.copyWith(fontSize: 20.sp),
                    textAlign: TextAlign.center,
                  ),
                  AppText(widget.property.title, textAlign: TextAlign.center),
                  AppText(
                    LocaleKeys.ownerPropertiesDeleteConfirmation,
                    textAlign: TextAlign.center,
                  ),
                  if (state.isLoading) const LinearProgressIndicator(),
                  if (state.isError && state.msg?.isNotEmpty == true)
                    AppText(state.msg!, color: AppColors.red),
                  DefaultButton(
                    title: LocaleKeys.ownerPropertiesDelete,
                    color: AppColors.red,
                    onTap: state.isLoading ? null : _deleteProperty,
                  ),
                  TextButton(
                    onPressed: state.isLoading ? null : Go.back,
                    child: AppText(LocaleKeys.cancel),
                  ),
                ],
              ),
            ),
          ),
        ),
      );
}
