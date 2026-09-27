class Screen {
  // Private constructor to prevent instantiation (acts like an 'object' or namespace)
  Screen._();

  static const String splash = '/splash';

  // Bottom nav roots
  static const String home = '/home';
  static const String lots = '/lots';
  static const String scan = '/scan';
  static const String review = '/review';
  static const String more = '/more';

  // Secondary destinations
  static const String newLot = '/new_lot';
  static const String profile = '/profile';
  static const String reports = '/reports';
  static const String offlineSync = '/offline_sync';

  // --- Dynamic Routes ---

  // Lot Details
  static const String lotDetails = '/lot_details/:lotId';
  static String createLotDetailsRoute(String lotId) => '/lot_details/$lotId';

  // Inspection
  static const String inspection = '/inspection/:lotId';
  static String createInspectionRoute(String lotId) => '/inspection/$lotId';

  // Grading Result
  static const String gradingResult = '/grading_result/:lotId';
  static String createGradingResultRoute(String lotId) => '/grading_result/$lotId';

  // Farmer Details
  static const String farmerDetails = '/farmer_details/:farmerId';
  static String createFarmerDetailsRoute(String farmerId) => '/farmer_details/$farmerId';
}