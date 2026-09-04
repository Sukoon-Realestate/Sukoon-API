part of '../../imports.dart';

class OwnerEditPropertyScreen extends StatefulWidget {
  const OwnerEditPropertyScreen({super.key, required this.property});

  final OwnerPropertyContent property;

  @override
  State<OwnerEditPropertyScreen> createState() =>
      _OwnerEditPropertyScreenState();
}

class _OwnerEditPropertyScreenState extends State<OwnerEditPropertyScreen> {
  late final TextEditingController _titleController;
  late final TextEditingController _priceController;
  late final TextEditingController _bedroomsController;
  late final TextEditingController _areaController;
  late final TextEditingController _descriptionController;
  late int _photoCount;

  @override
  void initState() {
    super.initState();
    _titleController = TextEditingController(text: widget.property.title);
    _priceController = TextEditingController(
      text: '${widget.property.monthlyPrice}',
    );
    _bedroomsController = TextEditingController(
      text: '${widget.property.bedrooms}',
    );
    _areaController = TextEditingController(text: '${widget.property.area}');
    _descriptionController = TextEditingController(
      text: widget.property.description,
    );
    _photoCount = widget.property.photoCount;
  }

  @override
  void dispose() {
    _titleController.dispose();
    _priceController.dispose();
    _bedroomsController.dispose();
    _areaController.dispose();
    _descriptionController.dispose();
    super.dispose();
  }

  void _save() {
    final String title = _titleController.text.trim();
    if (title.isEmpty) {
      _showMessage(LocaleKeys.ownerPropertiesNameRequired);
      return;
    }
    final OwnerPropertyContent updated = widget.property.copyWith(
      title: title,
      monthlyPrice:
          int.tryParse(_priceController.text) ?? widget.property.monthlyPrice,
      bedrooms:
          int.tryParse(_bedroomsController.text) ?? widget.property.bedrooms,
      area: int.tryParse(_areaController.text) ?? widget.property.area,
      description: _descriptionController.text.trim(),
      photoCount: _photoCount,
      status: widget.property.status.isRejected
          ? OwnerPropertyStatus.pending
          : widget.property.status,
    );
    Go.back(OwnerPropertyEditResult.saved(updated));
  }

  void _delete() {
    Go.back(OwnerPropertyEditResult.deleted(widget.property));
  }

  void _preview() {
    _showMessage(LocaleKeys.ownerPropertiesPreviewMessage);
  }

  void _showMessage(String message) {
    ScaffoldMessenger.of(context)
      ..hideCurrentSnackBar()
      ..showSnackBar(SnackBar(content: AppText(message)));
  }

  @override
  Widget build(BuildContext context) {
    return Directionality(
      textDirection: TextDirection.rtl,
      child: Scaffold(
        backgroundColor: AppColors.scaffoldBackground,
        body: SafeArea(
          child: Column(
            children: [
              OwnerPropertyTopBar(
                title: LocaleKeys.ownerPropertiesEditTitle,
                trailing: TextButton(
                  key: const ValueKey('owner-edit-delete'),
                  onPressed: _delete,
                  child: AppText(
                    LocaleKeys.ownerPropertiesDelete,
                    color: AppColors.red,
                    fontSize: 13.sp,
                    fontWeight: FontWeight.w800,
                  ),
                ),
              ),
              Expanded(
                child: ListView(
                  padding: EdgeInsets.fromLTRB(20.w, 8.h, 20.w, 24.h),
                  children: [
                    OwnerPropertyPhotosEditor(
                      photoCount: _photoCount,
                      onAddPressed: () => setState(() => _photoCount++),
                      onRemovePressed: () {
                        if (_photoCount > 0) {
                          setState(() => _photoCount--);
                        }
                      },
                    ),
                    18.szH,
                    OwnerEditField(
                      label: LocaleKeys.ownerPropertiesName,
                      controller: _titleController,
                    ),
                    14.szH,
                    OwnerEditField(
                      label: LocaleKeys.ownerPropertiesMonthlyPrice,
                      controller: _priceController,
                      keyboardType: TextInputType.number,
                      suffixText: LocaleKeys.ownerPropertiesCurrency,
                    ),
                    14.szH,
                    Row(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Expanded(
                          child: OwnerEditField(
                            label: LocaleKeys.ownerPropertiesBedrooms,
                            controller: _bedroomsController,
                            keyboardType: TextInputType.number,
                          ),
                        ),
                        12.szW,
                        Expanded(
                          child: OwnerEditField(
                            label: LocaleKeys.ownerPropertiesArea,
                            controller: _areaController,
                            keyboardType: TextInputType.number,
                            suffixText: LocaleKeys.ownerPropertiesSquareMeter,
                          ),
                        ),
                      ],
                    ),
                    14.szH,
                    OwnerEditField(
                      label: LocaleKeys.ownerPropertiesDescription,
                      controller: _descriptionController,
                      maxLines: 4,
                    ),
                    24.szH,
                    DefaultButton(
                      key: const ValueKey('owner-edit-save'),
                      title: LocaleKeys.ownerPropertiesSaveChanges,
                      onTap: _save,
                      height: 50.h,
                      borderRadius: BorderRadius.circular(15.r),
                      fontWeight: FontWeight.w900,
                    ),
                    12.szH,
                    DefaultButton(
                      key: const ValueKey('owner-edit-preview'),
                      title: LocaleKeys.ownerPropertiesPreview,
                      onTap: _preview,
                      height: 50.h,
                      color: AppColors.white,
                      textColor: AppColors.sokoonTeal,
                      borderColor: AppColors.sokoonTeal,
                      borderRadius: BorderRadius.circular(15.r),
                      fontWeight: FontWeight.w900,
                    ),
                  ],
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }
}
