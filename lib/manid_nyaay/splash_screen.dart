import 'dart:async';

import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';
import 'package:google_fonts/google_fonts.dart';
import 'package:lucide_icons_flutter/lucide_icons.dart';
import 'package:sih2631/manid_nyaay/data/routes/route_paths.dart';

// Note: AppAssets import removed since we are using direct paths based on your folder structure.

/// Clean, pixel-accurate Mandi Nyaay Splash Screen.
class SplashScreen extends StatefulWidget {
  const SplashScreen({super.key});

  @override
  State<SplashScreen> createState() => _SplashScreenState();
}

class _SplashScreenState extends State<SplashScreen>
    with SingleTickerProviderStateMixin {
  Timer? _navigationTimer;
  late final AnimationController _progressController;
  late final Animation<double> _progressAnimation;

  @override
  void initState() {
    super.initState();

    _progressController = AnimationController(
      vsync: this,
      duration: const Duration(milliseconds: 2600),
    );

    _progressAnimation = CurvedAnimation(
      parent: _progressController,
      curve: Curves.easeInOutCubic,
    );

    _progressController.forward();

    _navigationTimer = Timer(const Duration(milliseconds: 2000), () {
      if (mounted) {
        context.pushReplacement(RoutePaths.home);
      }
    });
  }

  @override
  void dispose() {
    _navigationTimer?.cancel();
    _progressController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: const Color(0xFF082255),
      body: Stack(
        fit: StackFit.expand,
        children: [
          // ─── 1. FULL-BLEED ORIGINAL SPLASH BACKGROUND ASSET ──────────
          Positioned.fill(
            child: Image.asset(
              'assets/images/splash/splash_background.png',
              fit: BoxFit.cover,
              alignment: Alignment.center,
              errorBuilder: (context, error, stackTrace) =>
                  Container(color: const Color(0xFF082255)),
            ),
          ),

          // ─── 2. TOP INSTITUTIONAL LOGOS & BRANDING ───────────────────
          Positioned(
            top: 0,
            left: 0,
            right: 0,
            child: SafeArea(
              bottom: false,
              child: Padding(
                padding: const EdgeInsets.symmetric(horizontal: 20),
                child: Column(
                  children: [
                    const SizedBox(height: 6),

                    // Top Bar: Ministry of Consumer Affairs & SIH 2026
                    Row(
                      mainAxisAlignment: MainAxisAlignment.spaceBetween,
                      crossAxisAlignment: CrossAxisAlignment.center,
                      children: [
                        Image.asset(
                          'assets/logos/splash/ministry_logo.png',
                          height: 48,
                          fit: BoxFit.contain,
                          errorBuilder: (context, error, stackTrace) =>
                          const SizedBox(height: 48),
                        ),
                        Image.asset(
                          'assets/logos/splash/sih_2026_logo.png',
                          height: 46,
                          fit: BoxFit.contain,
                          errorBuilder: (context, error, stackTrace) =>
                          const SizedBox(height: 46),
                        ),
                      ],
                    ),

                    const SizedBox(height: 14),

                    // Mandi Nyaay Onion Scanner Emblem
                    Image.asset(
                      'assets/logos/splash/mandi_nyaay_logo.png',
                      height: 86,
                      fit: BoxFit.contain,
                      errorBuilder: (context, error, stackTrace) =>
                      const SizedBox(height: 86),
                    ),

                    const SizedBox(height: 8),

                    // Brand Title: "Mandi Nyaay"
                    Text.rich(
                      TextSpan(
                        children: [
                          TextSpan(
                            text: 'Mandi ',
                            style: GoogleFonts.inter(
                              color: const Color(0xFF172554),
                              fontSize: 34,
                              fontWeight: FontWeight.w800,
                              letterSpacing: -0.6,
                            ),
                          ),
                          TextSpan(
                            text: 'Nyaay',
                            style: GoogleFonts.inter(
                              color: const Color(0xFF2563EB),
                              fontSize: 34,
                              fontWeight: FontWeight.w800,
                              letterSpacing: -0.6,
                            ),
                          ),
                        ],
                      ),
                    ),

                    const SizedBox(height: 4),

                    // Tagline
                    Text(
                      'Evidence-Backed Onion Grading',
                      style: GoogleFonts.inter(
                        color: const Color(0xFF1E293B),
                        fontSize: 15.5,
                        fontWeight: FontWeight.w600,
                        letterSpacing: -0.2,
                      ),
                    ),

                    const SizedBox(height: 5),

                    // Technical descriptor
                    Text(
                      'AI GRADING   •   TRUSTED MARKETS   •   ENHANCED FAIRNESS',
                      style: GoogleFonts.inter(
                        color: const Color(0xFF2563EB),
                        fontSize: 9.5,
                        fontWeight: FontWeight.w700,
                        letterSpacing: 0.8,
                      ),
                    ),
                  ],
                ),
              ),
            ),
          ),

          // ─── 3. BOTTOM LOADING & THREE BENEFIT COLUMNS ───────────────
          Positioned(
            left: 0,
            right: 0,
            bottom: 0,
            child: SafeArea(
              top: false,
              child: Padding(
                padding: const EdgeInsets.symmetric(horizontal: 20),
                child: Column(
                  mainAxisSize: MainAxisSize.min,
                  children: [
                    // "Loading..." label
                    Text(
                      'Loading...',
                      style: GoogleFonts.inter(
                        color: Colors.white,
                        fontSize: 14,
                        fontWeight: FontWeight.w500,
                        letterSpacing: 0.3,
                      ),
                    ),

                    const SizedBox(height: 10),

                    // Horizontal animated loading bar
                    Container(
                      width: 200,
                      height: 5.5,
                      decoration: BoxDecoration(
                        color: Colors.white.withAlpha(40),
                        borderRadius: BorderRadius.circular(10),
                      ),
                      child: AnimatedBuilder(
                        animation: _progressAnimation,
                        builder: (context, child) {
                          return FractionallySizedBox(
                            alignment: Alignment.centerLeft,
                            widthFactor: _progressAnimation.value,
                            child: Container(
                              decoration: BoxDecoration(
                                gradient: const LinearGradient(
                                  colors: [
                                    Color(0xFF38BDF8),
                                    Color(0xFF60A5FA),
                                  ],
                                ),
                                borderRadius: BorderRadius.circular(10),
                              ),
                            ),
                          );
                        },
                      ),
                    ),

                    const SizedBox(height: 30),

                    // Three Benefit Columns
                    Row(
                      crossAxisAlignment: CrossAxisAlignment.center,
                      children: [
                        // 1. For Farmers
                        const Expanded(
                          child: _BenefitColumn(
                            icon: LucideIcons.leaf,
                            iconColor: Color(0xFF34D399),
                            label: 'For Farmers',
                          ),
                        ),

                        // Divider
                        Container(
                          width: 1,
                          height: 32,
                          color: Colors.white.withAlpha(35),
                        ),

                        // 2. For Transparency
                        const Expanded(
                          child: _BenefitColumn(
                            icon: LucideIcons.shield,
                            iconColor: Color(0xFF818CF8),
                            label: 'For Transparency',
                          ),
                        ),

                        // Divider
                        Container(
                          width: 1,
                          height: 32,
                          color: Colors.white.withAlpha(35),
                        ),

                        // 3. For a Strong India
                        const Expanded(
                          child: _BenefitColumn(
                            icon: LucideIcons.trendingUp,
                            iconColor: Color(0xFFFBBF24),
                            label: 'For a Strong India',
                          ),
                        ),
                      ],
                    ),

                    const SizedBox(height: 16),
                  ],
                ),
              ),
            ),
          ),
        ],
      ),
    );
  }
}

class _BenefitColumn extends StatelessWidget {
  final IconData icon;
  final Color iconColor;
  final String label;

  const _BenefitColumn({
    required this.icon,
    required this.iconColor,
    required this.label,
  });

  @override
  Widget build(BuildContext context) {
    return Column(
      mainAxisSize: MainAxisSize.min,
      crossAxisAlignment: CrossAxisAlignment.center,
      children: [
        Icon(icon, size: 24, color: iconColor),
        const SizedBox(height: 6),
        Text(
          label,
          textAlign: TextAlign.center,
          style: GoogleFonts.inter(
            color: Colors.white.withAlpha(240),
            fontSize: 12,
            fontWeight: FontWeight.w500,
            letterSpacing: 0.1,
          ),
        ),
      ],
    );
  }
}