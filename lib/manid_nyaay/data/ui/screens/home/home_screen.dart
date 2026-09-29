import 'dart:math' as math;

import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';
import 'package:sih2631/manid_nyaay/data/domain/model/work_load_metrics.dart';
import 'package:sih2631/manid_nyaay/data/ui/components/lot_card.dart';
import 'package:sih2631/manid_nyaay/data/ui/components/mandi_app_bar.dart';
import 'package:sih2631/manid_nyaay/data/ui/components/work_load_metric_chip.dart';
import 'package:sih2631/manid_nyaay/data/ui/navigation/screen.dart';
import 'package:sih2631/manid_nyaay/data/ui/screens/home/home_view_model.dart';
import 'package:sih2631/manid_nyaay/data/ui/utils/responsive.dart';

// --- Theme Constants ---
const Color backgroundGray = Color(0xFFF4F5F7);
const Color institutionalBlue = Color(0xFF1565C0);
const Color statusOrange = Color(0xFFF57C00);
const Color statusAmber = Color(0xFFFFA000);
const Color statusGreen = Color(0xFF4CAF50);
const Color textPrimary = Color(0xFF1E293B);
const Color textSecondary = Color(0xFF64748B);
const Color textHint = Color(0xFF94A3B8);
const Color textOnBlue = Colors.white;
const Color surfaceWhite = Colors.white;
const Color onlineIndicator = Color(0xFF22C55E);

final BorderRadius mandiShapesMedium = BorderRadius.circular(12.0);

// --- MediaQuery helpers (move to responsive.dart if you prefer) ---
// --- Extra MediaQuery helpers (names chosen to not clash with responsive.dart) ---
extension HomeMediaQueryX on BuildContext {
  bool get isSmallPhone => MediaQuery.sizeOf(this).width < 360;

  /// 1.0 at 375dp wide, clamped so UI never gets tiny or huge.
  double get scale => (MediaQuery.sizeOf(this).width / 375).clamp(0.85, 1.3);

  /// Scale a design value (font, icon, spacing).
  double sp(double v) => v * scale;

  /// Keeps content readable on tablets / landscape.
  double get contentMaxWidth => 720;

  /// Safe-area bottom (gesture bar). Your `bottomInset` is the keyboard inset.
  double get safeBottom => MediaQuery.paddingOf(this).bottom;
}

class HomeScreen extends StatefulWidget {
  const HomeScreen({super.key});

  @override
  State<HomeScreen> createState() => _HomeScreenState();
}

class _HomeScreenState extends State<HomeScreen> {
  late final HomeViewModel _viewModel;

  @override
  void initState() {
    super.initState();
    _viewModel = HomeViewModel();
  }

  @override
  void dispose() {
    _viewModel.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return ListenableBuilder(
      listenable: _viewModel,
      builder: (context, _) {
        final state = _viewModel.uiState;

        // ── MediaQuery-derived layout values ─────────────────────────────
        final double hPad = context.responsivePadding(16.0);
        final double contentWidth =
            math.min(context.screenWidth, context.contentMaxWidth) - hPad * 2;
        final double bannerImageSize =
        (context.screenWidth * 0.24).clamp(80.0, 140.0);
        const double gap = 10.0;
        final bool twoColumns = context.isTablet;
        final double cardWidth =
        twoColumns ? (contentWidth - gap) / 2 : contentWidth;

        // ── Market price cards (live data or fallback) ───────────────────
        final List<Widget> priceCards = state.mandiPrices.isNotEmpty
            ? state.mandiPrices
            .take(4)
            .map<Widget>(
              (p) => _MarketPriceCard(
            title: "${p.commodity} (Modal)",
            location:
            "${p.market}, ${p.district} (${p.minPrice.toInt()}-${p.maxPrice.toInt()}/q · ${p.arrivalsTonnes}T)",
            price: "₹${p.modalPrice.toInt()}/q",
            isPositive: p.modalPrice >= 2000,
            color: p.modalPrice >= 2000 ? statusGreen : statusAmber,
          ),
        )
            .toList()
            : const <Widget>[
          _MarketPriceCard(
            title: "Grade-A Onion",
            location: "Lasalgaon Mandi Yard (Data.gov.in Feed)",
            price: "₹2,150/q",
            isPositive: true,
            color: statusGreen,
          ),
          _MarketPriceCard(
            title: "Medium APMC Onion",
            location: "Pimpalgaon Baswant (Agmarknet Live)",
            price: "₹2,180/q",
            isPositive: true,
            color: statusGreen,
          ),
          _MarketPriceCard(
            title: "Azadpur Terminal",
            location: "Azadpur APMC Delhi (Agmarknet Live)",
            price: "₹2,500/q",
            isPositive: true,
            color: statusGreen,
          ),
        ];

        return Scaffold(
          backgroundColor: backgroundGray,
          appBar: MandiTopAppBar(
            title: "MandiProof",
            subtitle: "Nashik APMC",
            showNotifications: true,
            showAvatar: true,
            avatarInitials: state.inspector.initials,
          ),
          body: state.isLoading
              ? const Center(
            child: CircularProgressIndicator(color: institutionalBlue),
          )
              : SafeArea(
            top: false, // AppBar already handles the top inset
            child: SingleChildScrollView(
              child: Center(
                child: ConstrainedBox(
                  constraints:
                  BoxConstraints(maxWidth: context.contentMaxWidth),
                  child: Padding(
                    padding: EdgeInsets.symmetric(horizontal: hPad),
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        const SizedBox(height: 14.0),

                        // ── Live Backend Status Card ────────────────
                        Container(
                          padding: const EdgeInsets.symmetric(
                              horizontal: 14.0, vertical: 10.0),
                          decoration: BoxDecoration(
                            color: surfaceWhite,
                            borderRadius: BorderRadius.circular(12.0),
                            boxShadow: [
                              BoxShadow(
                                color: Colors.black.withOpacity(0.04),
                                blurRadius: 4.0,
                                offset: const Offset(0, 2),
                              ),
                            ],
                          ),
                          child: Row(
                            children: [
                              // Connection dot
                              Container(
                                width: 10,
                                height: 10,
                                decoration: BoxDecoration(
                                  shape: BoxShape.circle,
                                  color: state.syncStatus.isOnline
                                      ? onlineIndicator
                                      : Colors.red,
                                ),
                              ),
                              const SizedBox(width: 8),
                              Expanded(
                                child: Column(
                                  crossAxisAlignment:
                                  CrossAxisAlignment.start,
                                  children: [
                                    Text(
                                      state.syncStatus.isOnline
                                          ? "Backend Connected"
                                          : "Backend Offline",
                                      overflow: TextOverflow.ellipsis,
                                      style: TextStyle(
                                        fontSize: context.sp(13),
                                        fontWeight: FontWeight.bold,
                                        color: state.syncStatus.isOnline
                                            ? onlineIndicator
                                            : Colors.red,
                                      ),
                                    ),
                                    Text(
                                      state.syncStatus.lastSyncedAt ??
                                          "Not synced yet",
                                      overflow: TextOverflow.ellipsis,
                                      style: TextStyle(
                                        fontSize: context.sp(11),
                                        color: textSecondary,
                                      ),
                                    ),
                                  ],
                                ),
                              ),
                              const SizedBox(width: 8),
                              // Inspector badge
                              Flexible(
                                child: Column(
                                  crossAxisAlignment:
                                  CrossAxisAlignment.end,
                                  children: [
                                    Text(
                                      state.inspector.name,
                                      overflow: TextOverflow.ellipsis,
                                      style: TextStyle(
                                        fontSize: context.sp(12),
                                        fontWeight: FontWeight.bold,
                                        color: textPrimary,
                                      ),
                                    ),
                                    Text(
                                      state.inspector.apmc,
                                      overflow: TextOverflow.ellipsis,
                                      style: TextStyle(
                                        fontSize: context.sp(11),
                                        color: textSecondary,
                                      ),
                                    ),
                                  ],
                                ),
                              ),
                              const SizedBox(width: 6),
                              Icon(
                                Icons.badge_outlined,
                                color: institutionalBlue,
                                size: context.sp(18),
                              ),
                            ],
                          ),
                        ),

                        const SizedBox(height: 14.0),

                        // ── Onion Grading & Procurement Banner ──────
                        Container(
                          padding: EdgeInsets.all(context.sp(16)),
                          decoration: BoxDecoration(
                            gradient: const LinearGradient(
                              colors: [
                                Color(0xFF1E3A8A),
                                institutionalBlue
                              ],
                              begin: Alignment.topLeft,
                              end: Alignment.bottomRight,
                            ),
                            borderRadius: BorderRadius.circular(14.0),
                          ),
                          child: Row(
                            children: [
                              Expanded(
                                child: Column(
                                  crossAxisAlignment:
                                  CrossAxisAlignment.start,
                                  children: [
                                    Text(
                                      "Onion Grading &\nProcurement",
                                      style: Theme.of(context)
                                          .textTheme
                                          .titleMedium
                                          ?.copyWith(
                                        color: textOnBlue,
                                        fontWeight: FontWeight.bold,
                                        height: 1.2,
                                        fontSize: context.sp(16),
                                      ),
                                    ),
                                    const SizedBox(height: 6.0),
                                    Text(
                                      "AI-assisted mass-weighted grading for APMC certified mandi inspection.",
                                      style: Theme.of(context)
                                          .textTheme
                                          .bodySmall
                                          ?.copyWith(
                                        color: textOnBlue
                                            .withOpacity(0.85),
                                        fontSize: context.sp(11),
                                      ),
                                    ),
                                    const SizedBox(height: 12.0),
                                    ElevatedButton(
                                      onPressed: () =>
                                          context.push(Screen.newLot),
                                      style: ElevatedButton.styleFrom(
                                        backgroundColor:
                                        const Color(0xFFFFB300),
                                        foregroundColor: textPrimary,
                                        padding:
                                        const EdgeInsets.symmetric(
                                            horizontal: 14.0,
                                            vertical: 8.0),
                                        shape: RoundedRectangleBorder(
                                          borderRadius:
                                          BorderRadius.circular(8.0),
                                        ),
                                      ),
                                      child: Text(
                                        "Begin Inspection ➔",
                                        style: TextStyle(
                                          fontWeight: FontWeight.bold,
                                          fontSize: context.sp(12),
                                        ),
                                      ),
                                    ),
                                  ],
                                ),
                              ),
                              // Hide image on very narrow phones
                              if (!context.isSmallPhone) ...[
                                const SizedBox(width: 12.0),
                                Container(
                                  width: bannerImageSize,
                                  height: bannerImageSize,
                                  decoration: BoxDecoration(
                                    color: Colors.white.withOpacity(0.15),
                                    borderRadius:
                                    BorderRadius.circular(12.0),
                                    image: const DecorationImage(
                                      image: AssetImage(
                                          'assets/logos/splash/mandi_nyaay_logo.png'),
                                      fit: BoxFit.cover,
                                    ),
                                  ),
                                ),
                              ],
                            ],
                          ),
                        ),

                        const SizedBox(height: 16.0),

                        // ── Workload metrics row ────────────────────
                        Row(
                          children: [
                            Expanded(
                              child: WorkloadMetricChip(
                                count: state.workloadMetrics.activeLots,
                                label: "Active",
                                accentColor: institutionalBlue,
                              ),
                            ),
                            const SizedBox(width: 10.0),
                            Expanded(
                              child: WorkloadMetricChip(
                                count: state.workloadMetrics.reviewNeeded,
                                label: "Review",
                                accentColor: statusOrange,
                              ),
                            ),
                            const SizedBox(width: 10.0),
                            Expanded(
                              child: WorkloadMetricChip(
                                count: state.workloadMetrics.syncPending,
                                label: "Pending",
                                accentColor: statusAmber,
                              ),
                            ),
                          ],
                        ),

                        const SizedBox(height: 20.0),

                        // ── Market Prices Section ───────────────────
                        Row(
                          mainAxisAlignment:
                          MainAxisAlignment.spaceBetween,
                          children: [
                            Flexible(
                              child: Row(
                                children: [
                                  Flexible(
                                    child: Text(
                                      "Daily Mandi Rates",
                                      overflow: TextOverflow.ellipsis,
                                      style: Theme.of(context)
                                          .textTheme
                                          .titleMedium
                                          ?.copyWith(
                                        fontWeight: FontWeight.bold,
                                        color: textPrimary,
                                      ),
                                    ),
                                  ),
                                  const SizedBox(width: 8),
                                  Container(
                                    padding: const EdgeInsets.symmetric(
                                        horizontal: 6, vertical: 2),
                                    decoration: BoxDecoration(
                                      color: const Color(0xFFE8F5E9),
                                      borderRadius:
                                      BorderRadius.circular(4),
                                      border: Border.all(
                                          color:
                                          const Color(0xFF81C784)),
                                    ),
                                    child: Text(
                                      "Data.gov.in Live",
                                      style: TextStyle(
                                        fontSize: context.sp(10),
                                        fontWeight: FontWeight.bold,
                                        color: const Color(0xFF2E7D32),
                                      ),
                                    ),
                                  ),
                                ],
                              ),
                            ),
                            TextButton(
                              onPressed: () => _viewModel.refresh(),
                              child: Text(
                                "Refresh",
                                style: Theme.of(context)
                                    .textTheme
                                    .labelMedium
                                    ?.copyWith(color: institutionalBlue),
                              ),
                            ),
                          ],
                        ),
                        const SizedBox(height: 6.0),

                        // 1 column on phones, 2 on tablets
                        Wrap(
                          spacing: gap,
                          runSpacing: 8.0,
                          children: [
                            for (final card in priceCards)
                              SizedBox(width: cardWidth, child: card),
                          ],
                        ),

                        const SizedBox(height: 20.0),

                        // ── Continue Inspection ─────────────────────
                        if (state.recentSessions.isNotEmpty) ...[
                          Row(
                            mainAxisAlignment:
                            MainAxisAlignment.spaceBetween,
                            crossAxisAlignment: CrossAxisAlignment.center,
                            children: [
                              Text(
                                "Continue Inspection",
                                style: Theme.of(context)
                                    .textTheme
                                    .titleMedium
                                    ?.copyWith(
                                  fontWeight: FontWeight.bold,
                                  color: textPrimary,
                                ),
                              ),
                              TextButton(
                                onPressed: () =>
                                    context.push(Screen.lots),
                                child: Text(
                                  "View All",
                                  style: Theme.of(context)
                                      .textTheme
                                      .labelMedium
                                      ?.copyWith(
                                      color: institutionalBlue),
                                ),
                              ),
                            ],
                          ),
                          const SizedBox(height: 10.0),
                          Wrap(
                            spacing: gap,
                            runSpacing: 10.0,
                            children: [
                              for (final lot in state.recentSessions)
                                SizedBox(
                                  width: cardWidth,
                                  child: LotCard(
                                    lot: lot,
                                    onContinue: () => context.push(
                                      Screen.createLotDetailsRoute(
                                          lot.id),
                                    ),
                                    onOpenCase: () => context.push(
                                      Screen.createLotDetailsRoute(
                                          lot.id),
                                    ),
                                  ),
                                ),
                            ],
                          ),
                        ],

                        const SizedBox(height: 12.0),
                        _OfflineSecureBanner(
                            syncStatus: state.syncStatus),
                        SizedBox(height: 24.0 + context.bottomInset),
                      ],
                    ),
                  ),
                ),
              ),
            ),
          ),
        );
      },
    );
  }
}

// ── Private Sub-Components ───────────────────────────────────────────────────

class _QuickActionItem extends StatelessWidget {
  final IconData icon;
  final String label;
  final VoidCallback onTap;

  const _QuickActionItem({
    required this.icon,
    required this.label,
    required this.onTap,
  });

  @override
  Widget build(BuildContext context) {
    return GestureDetector(
      onTap: onTap,
      child: Column(
        children: [
          Container(
            width: context.sp(56),
            height: context.sp(56),
            decoration: BoxDecoration(
              color: surfaceWhite,
              shape: BoxShape.circle,
              boxShadow: [
                BoxShadow(
                  color: Colors.black.withOpacity(0.05),
                  blurRadius: 4.0,
                  offset: const Offset(0, 2),
                ),
              ],
            ),
            alignment: Alignment.center,
            child: Icon(icon, color: institutionalBlue, size: context.sp(24)),
          ),
          const SizedBox(height: 6.0),
          Text(
            label,
            style: Theme.of(context).textTheme.labelSmall?.copyWith(
              color: textPrimary,
              fontWeight: FontWeight.w600,
            ),
          ),
        ],
      ),
    );
  }
}

class _MarketPriceCard extends StatelessWidget {
  final String title;
  final String location;
  final String price;
  final bool isPositive;
  final Color color;

  const _MarketPriceCard({
    required this.title,
    required this.location,
    required this.price,
    required this.isPositive,
    required this.color,
  });

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 14.0, vertical: 10.0),
      decoration: BoxDecoration(
        color: surfaceWhite,
        borderRadius: BorderRadius.circular(10.0),
        border: Border.all(color: const Color(0xFFE2E8F0), width: 0.8),
      ),
      child: Row(
        children: [
          Container(
            width: 10.0,
            height: 10.0,
            decoration: BoxDecoration(color: color, shape: BoxShape.circle),
          ),
          const SizedBox(width: 10.0),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  title,
                  maxLines: 1,
                  overflow: TextOverflow.ellipsis,
                  style: Theme.of(context).textTheme.labelMedium?.copyWith(
                    fontWeight: FontWeight.bold,
                    color: textPrimary,
                  ),
                ),
                Text(
                  location,
                  maxLines: 2,
                  overflow: TextOverflow.ellipsis,
                  style: Theme.of(context).textTheme.bodySmall?.copyWith(
                    color: textSecondary,
                    fontSize: context.sp(11),
                  ),
                ),
              ],
            ),
          ),
          const SizedBox(width: 8.0),
          Icon(
            isPositive ? Icons.arrow_upward : Icons.arrow_downward,
            color: color,
            size: 14.0,
          ),
          const SizedBox(width: 2.0),
          Text(
            price,
            style: Theme.of(context).textTheme.titleSmall?.copyWith(
              fontWeight: FontWeight.bold,
              color: textPrimary,
            ),
          ),
        ],
      ),
    );
  }
}

class _OfflineSecureBanner extends StatelessWidget {
  final SyncStatus syncStatus;

  const _OfflineSecureBanner({required this.syncStatus});

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 16.0),
      child: Row(
        mainAxisAlignment: MainAxisAlignment.center,
        crossAxisAlignment: CrossAxisAlignment.center,
        children: [
          const Icon(Icons.lock, color: textHint, size: 14.0),
          const SizedBox(width: 6.0),
          Flexible(
            child: Text(
              "Data is secured offline on this device",
              overflow: TextOverflow.ellipsis,
              style: Theme.of(context).textTheme.bodySmall?.copyWith(
                color: textHint,
              ),
            ),
          ),
        ],
      ),
    );
  }
}