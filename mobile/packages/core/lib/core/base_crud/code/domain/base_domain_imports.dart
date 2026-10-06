import 'dart:developer';
import 'package:equatable/equatable.dart';
import 'package:injectable/injectable.dart';
import 'package:multiple_result/multiple_result.dart';

import '../../../error/failure.dart';
import '../../../network/network_request.dart';
import 'entities/country_entity.dart';
import 'entities/faqs.dart';
import 'usecases/pagination_response.dart';

part 'entities/async.dart';
part 'entities/base_name_and_id_entity.dart';
part 'repositories/base_repository.dart';
part 'usecases/base_crud.dart';
part 'usecases/get_base_id_and_name_usecase.dart';
