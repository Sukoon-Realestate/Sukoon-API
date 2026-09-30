part of '../../../imports.dart';

class ProfileDeleteAccountButton extends StatefulWidget {
  const ProfileDeleteAccountButton({super.key});

  @override
  State<ProfileDeleteAccountButton> createState() =>
      _ProfileDeleteAccountButtonState();
}

class _ProfileDeleteAccountButtonState
    extends State<ProfileDeleteAccountButton> {
  late final ProfileDeleteAccountCubit _deleteCubit;

  @override
  void initState() {
    super.initState();
    _deleteCubit = ProfileDeleteAccountCubit();
  }

  @override
  void dispose() {
    _deleteCubit.close();
    super.dispose();
  }

  Future<bool> _confirmDeletion() async {
    final bool? shouldDelete = await showDialog<bool>(
      context: context,
      builder: (_) => const _ProfileDeleteAccountDialog(),
    );
    return shouldDelete == true;
  }

  Future<void> _deleteAccount() async {
    if (_deleteCubit.isLoading || !await _confirmDeletion() || !mounted) {
      return;
    }

    bool wasDeleted = false;
    await _deleteCubit.deleteAccount(onSuccess: () => wasDeleted = true);
    if (!wasDeleted || !mounted) return;

    await NotificationDeviceData.unregisterCurrentDevice();
    await UserCubit.instance.logout();
  }

  @override
  Widget build(BuildContext context) {
    return BlocProvider<ProfileDeleteAccountCubit>.value(
      value: _deleteCubit,
      child:
          BlocBuilder<
            ProfileDeleteAccountCubit,
            AsyncState<Map<String, dynamic>>
          >(
            builder: (context, state) {
              return Semantics(
                button: true,
                label: LocaleKeys.deleteAccount,
                child: InkWell(
                  onTap: state.isLoading ? null : _deleteAccount,
                  borderRadius: BorderRadius.circular(16.r),
                  child: Container(
                    width: double.infinity,
                    padding: EdgeInsets.symmetric(vertical: 15.h),
                    decoration: BoxDecoration(
                      color: AppColors.white,
                      borderRadius: BorderRadius.circular(16.r),
                      border: Border.all(
                        color: AppColors.red.withValues(alpha: .28),
                      ),
                    ),
                    child: Row(
                      mainAxisAlignment: MainAxisAlignment.center,
                      spacing: 8.w,
                      children: [
                        if (state.isLoading)
                          SizedBox.square(
                            dimension: 18.r,
                            child: CircularProgressIndicator(
                              strokeWidth: 2.r,
                              color: AppColors.red,
                            ),
                          )
                        else
                          Icon(
                            Icons.delete_outline_rounded,
                            color: AppColors.red,
                            size: 18.r,
                          ),
                        AppText(
                          LocaleKeys.deleteAccount,
                          style: AppTextStyles.bold14.copyWith(
                            color: AppColors.red,
                            fontSize: 14.sp,
                            height: 1.45,
                          ),
                        ),
                      ],
                    ),
                  ),
                ),
              );
            },
          ),
    );
  }
}

class _ProfileDeleteAccountDialog extends StatelessWidget {
  const _ProfileDeleteAccountDialog();

  @override
  Widget build(BuildContext context) {
    return AlertDialog(
      backgroundColor: AppColors.white,
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(20.r)),
      title: Column(
        spacing: 12.h,
        children: [
          Container(
            width: 48.r,
            height: 48.r,
            alignment: Alignment.center,
            decoration: const BoxDecoration(
              color: AppColors.redPale,
              shape: BoxShape.circle,
            ),
            child: Icon(
              Icons.delete_outline_rounded,
              color: AppColors.red,
              size: 24.r,
            ),
          ),
          AppText(
            LocaleKeys.areYouSureYouWantToDeleteYourAccount,
            style: AppTextStyles.extraBold.copyWith(
              color: AppColors.sokoonNavy,
              fontSize: 16.sp,
            ),
            textAlign: TextAlign.center,
          ),
        ],
      ),
      content: AppText(
        LocaleKeys.deletingWillRemoveAllYourData,
        style: AppTextStyles.regular13.copyWith(
          color: AppColors.sokoonGray,
          fontSize: 13.sp,
          height: 1.5,
        ),
        textAlign: TextAlign.center,
      ),
      actionsAlignment: MainAxisAlignment.center,
      actions: [
        TextButton(
          onPressed: () => Go.back(false),
          child: AppText(
            LocaleKeys.cancel,
            style: AppTextStyles.bold13.copyWith(
              color: AppColors.sokoonGray,
              fontSize: 13.sp,
              height: 1.45,
            ),
          ),
        ),
        FilledButton(
          onPressed: () => Go.back(true),
          style: FilledButton.styleFrom(
            backgroundColor: AppColors.red,
            shape: RoundedRectangleBorder(
              borderRadius: BorderRadius.circular(10.r),
            ),
          ),
          child: AppText(
            LocaleKeys.deleteAccount,
            style: AppTextStyles.bold13.copyWith(
              color: AppColors.white,
              fontSize: 13.sp,
              height: 1.45,
            ),
          ),
        ),
      ],
    );
  }
}
