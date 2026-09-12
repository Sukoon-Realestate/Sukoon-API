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
  final GlobalKey<FormFieldState<ProfileGender>> _genderFieldKey =
      GlobalKey<FormFieldState<ProfileGender>>();
  late final TextEditingController _nameController;
  late final TextEditingController _phoneController;
  late final TextEditingController _emailController;
  late final ProfileEditCubit _editCubit;
  File? _avatar;
  ProfileGender _gender = ProfileGender.unspecified;

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
    _editCubit = ProfileEditCubit();
  }

  @override
  void dispose() {
    _nameController.dispose();
    _phoneController.dispose();
    _emailController.dispose();
    _editCubit.close();
    super.dispose();
  }

  String get _genderLabel {
    if (_gender.isMale) return LocaleKeys.profileMale;
    if (_gender.isFemale) return LocaleKeys.profileFemale;
    return LocaleKeys.notSetYet;
  }

  Future<void> _pickAvatar() async {
    final File? avatar = await Helpers.getImageFromCameraOrDevice();
    if (avatar != null && mounted) {
      setState(() => _avatar = avatar);
    }
  }

  Future<void> _pickGender() async {
    final ProfileGender? gender = await showModalBottomSheet<ProfileGender>(
      context: context,
      useSafeArea: true,
      backgroundColor: AppColors.white,
      shape: RoundedRectangleBorder(
        borderRadius: BorderRadius.vertical(top: Radius.circular(20.r)),
      ),
      builder: (_) => const _ProfileGenderSheet(),
    );
    if (gender != null && mounted) {
      _genderFieldKey.currentState?.didChange(gender);
      setState(() => _gender = gender);
    }
  }

  Widget _buildGenderField({required bool isSaving}) {
    return FormField<ProfileGender>(
      key: _genderFieldKey,
      initialValue: _gender,
      validator: (gender) => gender == null || gender.isUnspecified
          ? LocaleKeys.pleaseEnterTheGender
          : null,
      builder: (field) {
        return Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            _ProfileReadonlyField(
              label: LocaleKeys.gender,
              value: _genderLabel,
              onTap: isSaving ? null : _pickGender,
            ),
            if (field.hasError) ...[
              6.szH,
              AppText(
                field.errorText ?? '',
                color: AppColors.sokoonRose,
                fontSize: 11.sp,
              ),
            ],
          ],
        );
      },
    );
  }

  Future<void> _save() async {
    if (_editCubit.isLoading || _formKey.currentState?.validate() != true) {
      return;
    }

    bool wasUpdated = false;
    await _editCubit.editProfile(
      body: ProfileEditBody(
        avatar: _avatar,
        fullName: _nameController.text.trim(),
        gender: _gender.apiValue,
        phoneNumber: _phoneController.text.trim(),
      ),
      onSuccess: () => wasUpdated = true,
    );
    if (!wasUpdated || !mounted) return;

    final UserModel updatedUser = UserModel.fromJson({
      ...widget.initialValue.toJson(),
      'name': _nameController.text.trim(),
      'phone': _phoneController.text.trim(),
      'email': widget.initialValue.email,
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
    return BlocProvider<ProfileEditCubit>.value(
      value: _editCubit,
      child: BlocBuilder<ProfileEditCubit, AsyncState<Map<String, dynamic>>>(
        builder: (context, state) => _buildScaffold(isSaving: state.isLoading),
      ),
    );
  }

  Widget _buildScaffold({required bool isSaving}) {
    return Directionality(
      textDirection: TextDirection.rtl,
      child: Scaffold(
        backgroundColor: AppColors.scaffoldBackground,
        body: SafeArea(
          child: Column(
            children: [
              ProfileScreenHeader(
                title: _title,
                showBackButton: true,
                trailing: TextButton(
                  onPressed: isSaving ? null : _save,
                  child: isSaving
                      ? SizedBox.square(
                          dimension: 18.r,
                          child: CircularProgressIndicator(
                            strokeWidth: 2.r,
                            color: _accentColor,
                          ),
                        )
                      : AppText(
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
                            imageFile: _avatar,
                            accentColor: _accentColor,
                            backgroundColor: _accentColor,
                            size: 88,
                            useInitial: true,
                            badgeIcon: Icons.camera_alt_outlined,
                            onBadgePressed: isSaving ? null : _pickAvatar,
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
                        controller: _nameController,
                        label: LocaleKeys.fullName,
                        hintText: LocaleKeys.fullNameHint,
                        accentColor: _accentColor,
                        validator: Validators.validateName,
                      ),
                      14.szH,
                      SokoonPhoneField(
                        controller: _phoneController,
                        accentColor: _accentColor,
                        validator: Validators.validateEmpty,
                      ),
                      14.szH,
                      SokoonEmailField(
                        controller: _emailController,
                        accentColor: _accentColor,
                        action: TextInputAction.done,
                        readOnly: true,
                      ),
                      14.szH,
                      if (widget.userType.isOwner)
                        Column(
                          children: [
                            _ProfileReadonlyField(
                              label: LocaleKeys.city,
                              value: LocaleKeys.profileCairo,
                            ),
                            14.szH,
                            _buildGenderField(isSaving: isSaving),
                          ],
                        )
                      else ...[
                        _ProfileReadonlyField(
                          label: LocaleKeys.profileBirthDate,
                          value: LocaleKeys.notSetYet,
                        ),
                        14.szH,
                        _buildGenderField(isSaving: isSaving),
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
  const _ProfileReadonlyField({
    required this.label,
    required this.value,
    this.onTap,
  });

  final String label;
  final String value;
  final VoidCallback? onTap;

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
        Material(
          color: AppColors.white,
          borderRadius: BorderRadius.circular(12.r),
          child: InkWell(
            onTap: onTap,
            borderRadius: BorderRadius.circular(12.r),
            child: Container(
              width: double.infinity,
              padding: EdgeInsets.symmetric(horizontal: 16.w, vertical: 14.h),
              decoration: BoxDecoration(
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
          ),
        ),
      ],
    );
  }
}

class _ProfileGenderSheet extends StatelessWidget {
  const _ProfileGenderSheet();

  @override
  Widget build(BuildContext context) {
    return Directionality(
      textDirection: TextDirection.rtl,
      child: Padding(
        padding: EdgeInsets.fromLTRB(20.w, 18.h, 20.w, 24.h),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            AppText(
              LocaleKeys.gender,
              color: AppColors.sokoonNavy,
              fontSize: 16.sp,
              fontWeight: FontWeight.w900,
            ),
            10.szH,
            _ProfileGenderOption(
              label: LocaleKeys.profileMale,
              onTap: () => Go.back(ProfileGender.male),
            ),
            const Divider(height: 1, color: AppColors.sokoonBorder),
            _ProfileGenderOption(
              label: LocaleKeys.profileFemale,
              onTap: () => Go.back(ProfileGender.female),
            ),
          ],
        ),
      ),
    );
  }
}

class _ProfileGenderOption extends StatelessWidget {
  const _ProfileGenderOption({required this.label, required this.onTap});

  final String label;
  final VoidCallback onTap;

  @override
  Widget build(BuildContext context) {
    return ListTile(
      contentPadding: EdgeInsets.zero,
      title: AppText(
        label,
        color: AppColors.sokoonNavy,
        fontSize: 14.sp,
        fontWeight: FontWeight.w700,
      ),
      trailing: Icon(
        Icons.chevron_left_rounded,
        color: AppColors.sokoonGray,
        size: 20.r,
      ),
      onTap: onTap,
    );
  }
}
