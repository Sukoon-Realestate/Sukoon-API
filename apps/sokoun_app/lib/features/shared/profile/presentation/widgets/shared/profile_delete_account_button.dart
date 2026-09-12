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

    await UserCubit.instance.logout();
    if (mounted) Go.offAll(const LoginScreen());
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
                  key: const ValueKey('profile-delete-account'),
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
                        8.szW,
                        AppText(
                          LocaleKeys.deleteAccount,
                          color: AppColors.red,
                          fontSize: 14.sp,
                          fontWeight: FontWeight.w700,
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
          12.szH,
          AppText(
            LocaleKeys.areYouSureYouWantToDeleteYourAccount,
            color: AppColors.sokoonNavy,
            fontSize: 16.sp,
            fontWeight: FontWeight.w800,
            textAlign: TextAlign.center,
          ),
        ],
      ),
      content: AppText(
        LocaleKeys.deletingWillRemoveAllYourData,
        color: AppColors.sokoonGray,
        fontSize: 13.sp,
        textAlign: TextAlign.center,
        height: 1.5,
      ),
      actionsAlignment: MainAxisAlignment.center,
      actions: [
        TextButton(
          key: const ValueKey('profile-delete-cancel'),
          onPressed: () => Go.back(false),
          child: AppText(
            LocaleKeys.cancel,
            color: AppColors.sokoonGray,
            fontSize: 13.sp,
            fontWeight: FontWeight.w700,
          ),
        ),
        FilledButton(
          key: const ValueKey('profile-delete-confirm'),
          onPressed: () => Go.back(true),
          style: FilledButton.styleFrom(
            backgroundColor: AppColors.red,
            shape: RoundedRectangleBorder(
              borderRadius: BorderRadius.circular(10.r),
            ),
          ),
          child: AppText(
            LocaleKeys.deleteAccount,
            color: AppColors.white,
            fontSize: 13.sp,
            fontWeight: FontWeight.w700,
          ),
        ),
      ],
    );
  }
}
