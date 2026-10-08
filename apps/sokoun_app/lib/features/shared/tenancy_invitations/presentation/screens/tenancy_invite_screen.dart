import 'package:flutter/material.dart';
import 'package:flutter_bloc/flutter_bloc.dart';
import 'package:melos_core/config/language/locale_keys.g.dart';
import 'package:melos_core/core/base_crud/code/presentation/cubit/base_cubit/async_cubit.dart';
import 'package:sokoun_app/shared_widgets/app_scaffold.dart';
import 'package:sokoun_app/shared_widgets/sokoun_layout.dart';
import 'package:sokoun_app/features/shared/digital_leases/presentation/cubits/lease_property_cubit.dart';
import 'package:sokoun_app/features/shared/premium/presentation/widgets/shared/premium_remote_view.dart';
import 'package:sokoun_app/features/tenant/home/data/models/property_details_model.dart';
import '../../data/tenancy_invitation_capabilities.dart';
import '../../data/models/tenancy_invitation.dart';
import '../cubits/tenancy_invitation_create_cubit.dart';
import '../widgets/tenancy_invite_form.dart';

class TenancyInviteScreen extends StatefulWidget {
  const TenancyInviteScreen({
    super.key,
    required this.propertyId,
    required this.propertyTitle,
    required this.tenantId,
    required this.tenantName,
  });
  final String propertyId, propertyTitle, tenantId, tenantName;
  @override
  State<TenancyInviteScreen> createState() => _TenancyInviteScreenState();
}

class _TenancyInviteScreenState extends State<TenancyInviteScreen> {
  late final TenancyInvitationCreateCubit _createCubit;
  late final LeasePropertyCubit _propertyCubit;
  late final Future<void> _request;
  @override
  void initState() {
    super.initState();
    _createCubit = TenancyInvitationCreateCubit();
    _propertyCubit = LeasePropertyCubit();
    _request = TenancyInvitationCapabilities.current.enabled
        ? _propertyCubit.load(widget.propertyId)
        : Future<void>.value();
  }

  @override
  void dispose() {
    _createCubit.close();
    _propertyCubit.close();
    super.dispose();
  }

  Widget _form(PropertyDetailsModel property) => TenancyInviteForm(
    propertyId: widget.propertyId,
    propertyTitle: widget.propertyTitle,
    tenantId: widget.tenantId,
    tenantName: widget.tenantName,
    property: property,
    isFresh: !_propertyCubit.isCached,
    onRefresh: () => _propertyCubit.load(widget.propertyId),
  );

  @override
  Widget build(BuildContext context) => BlocProvider.value(
    value: _createCubit,
    child:
        BlocSelector<
          TenancyInvitationCreateCubit,
          AsyncState<TenancyInvitation>,
          bool
        >(
          selector: (state) => state.isLoading,
          builder: (context, isSending) => PopScope(
            canPop: !isSending,
            child: AppScaffold(
              title: LocaleKeys.tenancyInviteToRent,
              showBackButton: true,
              isBackEnabled: !isSending,
              body: SafeArea(
                child: SingleChildScrollView(
                  padding: const EdgeInsets.all(20),
                  child: SokounContent(
                    width: SokounContentWidth.form,
                    child: !TenancyInvitationCapabilities.current.enabled
                        ? _form(const PropertyDetailsModel.initial())
                        : PremiumRemoteView<
                            LeasePropertyCubit,
                            PropertyDetailsModel
                          >(
                            cubit: _propertyCubit,
                            request: _request,
                            initialData: const PropertyDetailsModel.initial(),
                            onRetry: () =>
                                _propertyCubit.load(widget.propertyId),
                            builder: _form,
                          ),
                  ),
                ),
              ),
            ),
          ),
        ),
  );
}
