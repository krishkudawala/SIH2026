import 'dart:async';

import 'package:sih2631/manid_nyaay/data/domain/model/work_load_metrics.dart';
import 'package:sih2631/manid_nyaay/data/domain/repository/lot_repository.dart';

// import 'package:mandi_nyaay/domain/model/workload_metrics.dart';
// import 'package:mandi_nyaay/domain/repository/lot_repository.dart';

class GetWorkloadMetricsUseCase {
  final LotRepository repository;

  const GetWorkloadMetricsUseCase(this.repository);

  // The call() method in Dart acts exactly like invoke() in Kotlin
  Future<WorkloadMetrics> call() async {
    return await repository.getWorkloadMetrics();
  }
}