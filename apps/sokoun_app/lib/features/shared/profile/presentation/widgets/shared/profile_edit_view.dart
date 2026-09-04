part of '../../../imports.dart';

class ProfileEditView extends StatefulWidget {
  const ProfileEditView({
    super.key,
    required this.initialValue,
    required this.userType,
  });

  final UserModel initialValue;
  final UserType userType;

  @override
  State<ProfileEditView> createState() => _ProfileEditViewState();
}

class _ProfileEditViewState extends State<ProfileEditView> {
  final GlobalKey<FormState> _formKey = GlobalKey<FormState>();
  late final TextEditingController _nameController;
  late final TextEditingController _phoneController;
  late final TextEditingController _emailController;
  bool _isSaving = false;

  Color get _accentColor =>
      widget.userType.isOwner ? AppColors.sokoonGold : AppColors.sokoonTeal;

  String get _title => widget.userType.isOwner
      ? LocaleKeys.profileOwnerEditTitle
      : LocaleKeys.profileTenantEditTitle;

  @override
  void initState() {
    super.initState();
    _nameController = TextEditingController(text: widget.initialValue.name);
    _phoneController = TextEditingController(text: widget.initialValue.phone);
    _emailController = TextEditingController(text: widget.initialValue.email);
  }

  @override
  void dispose() {
    _nameController.dispose();
    _phoneController.dispose();
    _emailController.dispose();
    super.dispose();
  }

  Future<void> _save() async {
    if (_isSaving || _formKey.currentState?.validate() != true) {
      return;
    }
    setState(() => _isSaving = true);

    final UserModel updatedUser = UserModel.fromJson({
      ...widget.initialValue.toJson(),
      'name': _nameController.text.trim(),
      'phone': _phoneController.text.trim(),
      'email': _emailController.text.trim(),
      'type': widget.userType.name,
    });
    await UserCubit.instance.updateUser(updatedUser);

    if (!mounted) {
      return;
    }
    MessageUtils.showSnackBar(
      LocaleKeys.profileUpdatedSuccessfully,
      backgroundColor: AppColors.green,
      textColor: AppColors.white,
      context: context,
    );
    Go.back(updatedUser);
  }

  @override
  Widget build(BuildContext context) {
    return Directionality(
      textDirection: TextDirection.rtl,
      child: Scaffold(
        key: ValueKey(widget.userType.isOwner ? 'O-EDIT-P-01' : 'T-EDIT-01'),
        backgroundColor: AppColors.scaffoldBackground,
        body: SafeArea(
          child: Column(
            children: [
              ProfileScreenHeader(
                title: _title,
                showBackButton: true,
                trailing: TextButton(
                  key: const ValueKey('profile-save'),
                  onPressed: _isSaving ? null : _save,
                  child: AppText(
                    LocaleKeys.profileSave,
                    color: _accentColor,
                    fontSize: 14.sp,
                    fontWeight: FontWeight.w700,
                  ),
                ),
              ),
              Expanded(
                child: Form(
                  key: _formKey,
                  child: ListView(
                    padding: EdgeInsets.fromLTRB(20.w, 24.h, 20.w, 28.h),
                    children: [
                      Column(
                        children: [
                          ProfileAvatar(
                            name: _nameController.text,
                            accentColor: _accentColor,
                            backgroundColor: _accentColor,
                            size: 88,
                            useInitial: true,
                            badgeIcon: Icons.camera_alt_outlined,
                          ),
                          8.szH,
                          AppText(
                            LocaleKeys.profileChangePhoto,
                            color: _accentColor,
                            fontSize: 13.sp,
                            fontWeight: FontWeight.w700,
                          ),
                        ],
                      ),
                      24.szH,
                      SokoonNameField(
                        key: const ValueKey('profile-name-field'),
                        controller: _nameController,
                        label: LocaleKeys.fullName,
                        hintText: LocaleKeys.fullNameHint,
                        accentColor: _accentColor,
                        validator: Validators.validateName,
                      ),
                      14.szH,
                      SokoonPhoneField(
                        key: const ValueKey('profile-phone-field'),
                        controller: _phoneController,
                        accentColor: _accentColor,
                        validator: Validators.validateEmpty,
                      ),
                      14.szH,
                      SokoonEmailField(
                        key: const ValueKey('profile-email-field'),
                        controller: _emailController,
                        accentColor: _accentColor,
                        action: TextInputAction.done,
                      ),
                      14.szH,
                      if (widget.userType.isOwner)
                        _ProfileReadonlyField(
                          label: LocaleKeys.city,
                          value: LocaleKeys.profileCairo,
                        )
                      else ...[
                        _ProfileReadonlyField(
                          label: LocaleKeys.profileBirthDate,
                          value: LocaleKeys.notSetYet,
                        ),
                        14.szH,
                        _ProfileReadonlyField(
                          label: LocaleKeys.gender,
                          value: LocaleKeys.profileMale,
                        ),
                      ],
                      if (widget.userType.isOwner) ...[
                        16.szH,
                        ProfileVerificationBanner(
                          title: LocaleKeys.profileVerifiedAccount,
                          description:
                              LocaleKeys.profileVerifiedAccountDescription,
                        ),
                      ],
                    ],
                  ),
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }
}

class _ProfileReadonlyField extends StatelessWidget {
  const _ProfileReadonlyField({required this.label, required this.value});

  final String label;
  final String value;

  @override
  Widget build(BuildContext context) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        AppText(
          label,
          color: AppColors.sokoonNavy,
          fontSize: 13.sp,
          fontWeight: FontWeight.w700,
        ),
        7.szH,
        Container(
          width: double.infinity,
          padding: EdgeInsets.symmetric(horizontal: 16.w, vertical: 14.h),
          decoration: BoxDecoration(
            color: AppColors.white,
            borderRadius: BorderRadius.circular(12.r),
            border: Border.all(color: AppColors.sokoonBorder),
          ),
          child: Row(
            children: [
              Expanded(
                child: AppText(
                  value,
                  color: AppColors.sokoonNavy,
                  fontSize: 14.sp,
                  fontWeight: FontWeight.w600,
                ),
              ),
              Icon(
                Icons.arrow_back_ios_new_rounded,
                color: AppColors.sokoonGray,
                size: 15.r,
              ),
            ],
          ),
        ),
      ],
    );
  }
}
