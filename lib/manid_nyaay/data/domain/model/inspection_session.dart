// --- Enums ---

enum BagTier {
  top("Top Tier"),
  middle("Middle Tier"),
  bottom("Bottom Tier");

  final String displayLabel;
  const BagTier(this.displayLabel);
}

enum CaptureOrientation {
  top("Top View", 1),
  side("Side View", 2),
  underside("Underside View", 3);

  final String displayLabel;
  final int stepNumber;
  const CaptureOrientation(this.displayLabel, this.stepNumber);
}

enum InspectionEventType {
  sessionStarted,
  bagSelected,
  captureStarted,
  captureCompleted,
  onionGraded,
  correspondenceUncertain,
  sampleAccepted,
  sessionPaused,
  sessionCompleted,
}

enum InspectionState {
  idle,
  sourceSelection,
  batchTopCapture,
  batchSideCapture,
  batchUndersideCapture,
  crossViewCorrespondence,
  perOnionResult,
  samplingSufficiency,
  finalResult,
}

// --- Data Classes ---

class InspectionSession {
  final String id;
  final String lotId;
  final DateTime startedAt;
  final InspectionState currentState;
  final List<BagSelection> selectedBags;
  final List<BatchCapture> batchCaptures;
  final List<InspectionEvent> events;

  const InspectionSession({
    required this.id,
    required this.lotId,
    required this.startedAt,
    required this.currentState,
    this.selectedBags = const [],
    this.batchCaptures = const [],
    this.events = const [],
  });

  InspectionSession copyWith({
    String? id,
    String? lotId,
    DateTime? startedAt,
    InspectionState? currentState,
    List<BagSelection>? selectedBags,
    List<BatchCapture>? batchCaptures,
    List<InspectionEvent>? events,
  }) {
    return InspectionSession(
      id: id ?? this.id,
      lotId: lotId ?? this.lotId,
      startedAt: startedAt ?? this.startedAt,
      currentState: currentState ?? this.currentState,
      selectedBags: selectedBags ?? this.selectedBags,
      batchCaptures: batchCaptures ?? this.batchCaptures,
      events: events ?? this.events,
    );
  }
}

class BagSelection {
  final int bagNumber;
  final BagTier tier;
  final bool selectedByInspector;
  final DateTime timestamp;

  BagSelection({
    required this.bagNumber,
    required this.tier,
    this.selectedByInspector = true,
    DateTime? timestamp,
  }) : timestamp = timestamp ?? DateTime.now();

  BagSelection copyWith({
    int? bagNumber,
    BagTier? tier,
    bool? selectedByInspector,
    DateTime? timestamp,
  }) {
    return BagSelection(
      bagNumber: bagNumber ?? this.bagNumber,
      tier: tier ?? this.tier,
      selectedByInspector: selectedByInspector ?? this.selectedByInspector,
      timestamp: timestamp ?? this.timestamp,
    );
  }
}

class BatchCapture {
  final String id;
  final String sessionId;
  final String bagId;
  final CaptureOrientation orientation;
  final DateTime capturedAt;
  final String? imageUri; // null = placeholder in Phase 1

  const BatchCapture({
    required this.id,
    required this.sessionId,
    required this.bagId,
    required this.orientation,
    required this.capturedAt,
    this.imageUri,
  });

  BatchCapture copyWith({
    String? id,
    String? sessionId,
    String? bagId,
    CaptureOrientation? orientation,
    DateTime? capturedAt,
    String? imageUri,
  }) {
    return BatchCapture(
      id: id ?? this.id,
      sessionId: sessionId ?? this.sessionId,
      bagId: bagId ?? this.bagId,
      orientation: orientation ?? this.orientation,
      capturedAt: capturedAt ?? this.capturedAt,
      imageUri: imageUri ?? this.imageUri,
    );
  }
}

class InspectionEvent {
  final String id;
  final String sessionId;
  final InspectionEventType eventType;
  final String? bagId;
  final DateTime timestamp;
  final Map<String, String> metadata;

  InspectionEvent({
    required this.id,
    required this.sessionId,
    required this.eventType,
    this.bagId,
    DateTime? timestamp,
    this.metadata = const {},
  }) : timestamp = timestamp ?? DateTime.now();

  InspectionEvent copyWith({
    String? id,
    String? sessionId,
    InspectionEventType? eventType,
    String? bagId,
    DateTime? timestamp,
    Map<String, String>? metadata,
  }) {
    return InspectionEvent(
      id: id ?? this.id,
      sessionId: sessionId ?? this.sessionId,
      eventType: eventType ?? this.eventType,
      bagId: bagId ?? this.bagId,
      timestamp: timestamp ?? this.timestamp,
      metadata: metadata ?? this.metadata,
    );
  }
}