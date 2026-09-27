import 'dart:async';
import 'package:sih2631/manid_nyaay/data/domain/model/inspection_session.dart';
import 'package:sih2631/manid_nyaay/data/domain/repository/inspection_repository.dart';
import 'package:uuid/uuid.dart';



class StartInspectionSessionUseCase {
  final InspectionRepository repository;

  // A const instance of Uuid can be reused
  final Uuid _uuid = const Uuid();

  StartInspectionSessionUseCase(this.repository);

  // Kotlin's 'invoke()' translates to Dart's 'call()'
  Future<InspectionSession> call(String lotId) async {
    final session = InspectionSession(
      id: _uuid.v4(), // Generates a random v4 UUID
      lotId: lotId,
      startedAt: DateTime.now(), // Equivalent to Instant.now()
      currentState: InspectionState.sourceSelection, // Mapped to camelCase enum value
    );

    await repository.createSession(session);

    return session;
  }
}