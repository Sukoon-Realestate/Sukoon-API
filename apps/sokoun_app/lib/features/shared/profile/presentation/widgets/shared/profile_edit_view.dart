part of '../../../imports.dart';

class ProfileEditView extends StatefulWidget {
  const ProfileEditView({
    super.key,
    required this.initialValue,
    required this.workspace,
  });

  final UserModel initialValue;
  final AppWorkspace workspace;

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
  final ValueNotifier<File?> _avatar = ValueNotifier<File?>(null);
  final ValueNotifier<ProfileGender> _gender = ValueNotifier<ProfileGender>(
    ProfileGender.unspecified,
  );

  Color get _accentColor =>
      widget.workspace.isOwner ? AppColors.sokoonGold : AppColors.sokoonTeal;

  String get _title => widget.workspace.isOwner
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
    _avatar.dispose();
    _gender.dispose();
    _editCubit.close();
    super.dispose();
  }

  String _genderLabel(ProfileGender gender) {
    if (gender.isMale) return LocaleKeys.profileMale;
    if (gender.isFemale) return LocaleKeys.profileFemale;
    return LocaleKeys.notSetYet;
  }

  Future<void> _pickAvatar() async {
    final File? avatar = await Helpers.getImageFromCameraOrDevice();
    if (avatar != null && mounted) {
      _avatar.value = avatar;
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
      _gender.value = gender;
    }
  }

  Widget _buildGenderField({required bool isSaving}) {
    return FormField<ProfileGender>(
      key: _genderFieldKey,
      initialValue: _gender.value,
      validator: (gender) => gender == null || gender.isUnspecified
          ? LocaleKeys.pleaseEnterTheGender
          : null,
      builder: (field) {
        return Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          spacing: 6.h,
          children: [
            ValueListenableBuilder<ProfileGender>(
              valueListenable: _gender,
              builder: (context, gender, _) => _ProfileReadonlyField(
                label: LocaleKeys.gender,
                value: _genderLabel(gender),
                onTap: isSaving ? null : _pickGender,
              ),
            ),
            if (field.hasError)
              AppText(
                field.errorText ?? '',
                style: AppTextStyles.regular11.copyWith(
                  color: AppColors.sokoonRose,
                  fontSize: 11.sp,
                  height: 1.45,
                ),
              ),
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
        avatar: _avatar.value,
        fullName: _nameController.text.trim(),
        gender: _gender.value.apiValue,
        phoneNumber: _phoneController.text.trim(),
      ),
      onSuccess: () => wasUpdated = true,
    );
    if (!wasUpdated || !mounted) return;

    final UserModel updatedUser = widget.initialValue.copyWith(
      name: _nameController.text.trim(),
      phone: _phoneController.text.trim(),
    );
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
      child: UnsavedChangesGuard(
        hasChanges: () =>
            _nameController.text.trim() != widget.initialValue.name ||
            _phoneController.text.trim() != widget.initialValue.phone ||
            _avatar.value != null ||
            !_gender.value.isUnspecified,
        isSaving: () => _editCubit.isLoading,
        child: _buildScaffold(),
      ),
    );
  }

  Widget _buildScaffold() {
    return AppScaffold(
      title: _title,
      showBackButton: true,
      actions: [
        BlocSelector<ProfileEditCubit, AsyncState<Map<String, dynamic>>, bool>(
          selector: (state) => state.isLoading,
          builder: (context, isSaving) => TextButton(
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
                    style: AppTextStyles.bold14.copyWith(
                      color: _accentColor,
                      fontSize: 14.sp,
                      height: 1.45,
                    ),
                  ),
          ),
        ),
      ],
      backgroundColor: AppColors.scaffoldBackground,
      body: SafeArea(
        child: Form(
          key: _formKey,
          child: ListView(
            padding: EdgeInsets.fromLTRB(20.w, 24.h, 20.w, 28.h),
            children: [
              ValueListenableBuilder<File?>(
                valueListenable: _avatar,
                builder: (context, avatar, _) => Column(
                  spacing: 8.h,
                  children: [
                    BlocSelector<
                      ProfileEditCubit,
                      AsyncState<Map<String, dynamic>>,
                      bool
                    >(
                      selector: (state) => state.isLoading,
                      builder: (context, isSaving) => ProfileAvatar(
                        name: _nameController.text,
                        imageFile: avatar,
                        accentColor: _accentColor,
                        backgroundColor: _accentColor,
                        size: 88,
                        useInitial: true,
                        badgeIcon: Icons.camera_alt_outlined,
                        onBadgePressed: isSaving ? null : _pickAvatar,
                      ),
                    ),
                    AppText(
                      LocaleKeys.profileChangePhoto,
                      style: AppTextStyles.bold13.copyWith(
                        color: _accentColor,
                        fontSize: 13.sp,
                        height: 1.45,
                      ),
                    ),
                  ],
                ),
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
              if (widget.workspace.isOwner)
                Column(
                  spacing: 14.h,
                  children: [
                    _ProfileReadonlyField(
                      label: LocaleKeys.city,
                      value: LocaleKeys.profileCairo,
                    ),
                    BlocSelector<
                      ProfileEditCubit,
                      AsyncState<Map<String, dynamic>>,
                      bool
                    >(
                      selector: (state) => state.isLoading,
                      builder: (context, isSaving) =>
                          _buildGenderField(isSaving: isSaving),
                    ),
                  ],
                )
              else ...[
                _ProfileReadonlyField(
                  label: LocaleKeys.profileBirthDate,
                  value: LocaleKeys.notSetYet,
                ),
                14.szH,
                BlocSelector<
                  ProfileEditCubit,
                  AsyncState<Map<String, dynamic>>,
                  bool
                >(
                  selector: (state) => state.isLoading,
                  builder: (context, isSaving) =>
                      _buildGenderField(isSaving: isSaving),
                ),
              ],
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
      spacing: 7.h,
      children: [
        AppText(
          label,
          style: AppTextStyles.bold13.copyWith(
            color: AppColors.sokoonNavy,
            fontSize: 13.sp,
            height: 1.45,
          ),
        ),
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
                      style: AppTextStyles.semiBold.copyWith(
                        color: AppColors.sokoonNavy,
                        fontSize: 14.sp,
                      ),
                    ),
                  ),
                  Icon(
                    Icons.arrow_forward_ios_rounded,
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
    return Padding(
      padding: EdgeInsets.fromLTRB(20.w, 18.h, 20.w, 24.h),
      child: Column(
        mainAxisSize: MainAxisSize.min,
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          AppText(
            LocaleKeys.gender,
            style: AppTextStyles.bold16.copyWith(
              color: AppColors.sokoonNavy,
              fontSize: 16.sp,
              height: 1.45,
            ),
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
        style: AppTextStyles.bold14.copyWith(
          color: AppColors.sokoonNavy,
          fontSize: 14.sp,
          height: 1.45,
        ),
      ),
      trailing: Icon(
        Icons.chevron_right_rounded,
        color: AppColors.sokoonGray,
        size: 20.r,
      ),
      onTap: onTap,
    );
  }
}
