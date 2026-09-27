import 'package:injectable/injectable.dart';
import 'package:multiple_result/multiple_result.dart';

import '../../../error/failure.dart';
import '../../../extensions/error_handler_extension.dart';
import '../../../extensions/object.dart';
import '../../../local_db/objectbox_cache_service.dart';
import '../../../network/network_request.dart';
import '../../../network/network_service.dart';
import '../../../network/account_session.dart';
import '../domain/base_domain_imports.dart';
import '../domain/usecases/pagination_response.dart';

part 'datasources/base_local_data_source.dart';
part 'datasources/base_remote_data_source.dart';
part 'repositories/base_repository_impl.dart';
