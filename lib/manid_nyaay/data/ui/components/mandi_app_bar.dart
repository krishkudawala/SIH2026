import 'package:flutter/material.dart';
import 'package:sih2631/manid_nyaay/data/api/api_config.dart';
import 'package:sih2631/manid_nyaay/data/ui/utils/responsive.dart';

// Note: Replace these with your actual theme colors
// equivalent to your com.mandiNyaay.ui.theme colors
const Color blueDark = Color(0xFF0F2B46); // Placeholder
const Color textOnBlue = Colors.white;
const Color blueMedium = Colors.blueAccent;

class MandiTopAppBar extends StatelessWidget implements PreferredSizeWidget {
  final String title;
  final String? subtitle;
  final bool showBack;
  final bool showNotifications;
  final bool showAvatar;
  final String avatarInitials;
  final VoidCallback? onBack;
  final VoidCallback? onNotifications;
  final VoidCallback? onAvatar;

  const MandiTopAppBar({
    super.key,
    required this.title,
    this.subtitle,
    this.showBack = false,
    this.showNotifications = false,
    this.showAvatar = false,
    this.avatarInitials = "RS",
    this.onBack,
    this.onNotifications,
    this.onAvatar,
  });

  // preferredSize has no BuildContext, so the bar height stays fixed at 64.
  // Everything INSIDE the bar is scaled with MediaQuery in build().
  @override
  Size get preferredSize => const Size.fromHeight(64.0);

  @override
  Widget build(BuildContext context) {
    // ── MediaQuery values ────────────────────────────────────────────────
    final double width = MediaQuery.sizeOf(context).width;
    // Capped at 1.15 so content always fits inside the fixed 64dp bar.
    final double scale = (width / 375).clamp(0.85, 1.15);
    final bool isCompact = width < 360; // very small phones

    final double iconSize = 24.0 * scale;
    final double avatarSize = 36.0 * scale;
    final double statusIconSize = 14.0 * scale;
    final double statusFontSize = 10.0 * scale;

    final TextStyle? titleBase = Theme.of(context).textTheme.titleLarge;
    final TextStyle? subtitleBase = Theme.of(context).textTheme.labelSmall;
    final double titleFontSize = (titleBase?.fontSize ?? 22.0) * scale;
    final double subtitleFontSize = (subtitleBase?.fontSize ?? 11.0) * scale;

    // Material perfectly replicates Compose's Surface
    return Material(
      color: blueDark,
      elevation: 4.0, // shadowElevation
      child: SafeArea(
        bottom: false, // Replicates statusBarsPadding()
        child: Container(
          height: 64.0,
          padding: EdgeInsets.symmetric(
            horizontal: context.responsivePadding(8.0),
          ),
          child: Row(
            crossAxisAlignment: CrossAxisAlignment.center, // verticalAlignment = Alignment.CenterVertically
            children: [
              // Back Button or Spacer
              if (showBack)
                IconButton(
                  icon: const Icon(Icons.arrow_back), // Auto-mirrored natively in Flutter
                  iconSize: iconSize,
                  color: textOnBlue,
                  onPressed: onBack,
                )
              else
                const SizedBox(width: 8.0),

              // Title and Subtitle Column
              Expanded( // Modifier.weight(1f)
                child: Column(
                  mainAxisAlignment: MainAxisAlignment.center,
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      title,
                      maxLines: 1,
                      overflow: TextOverflow.ellipsis,
                      style: titleBase?.copyWith(
                        color: textOnBlue,
                        fontWeight: FontWeight.w800, // ExtraBold
                        letterSpacing: -0.5,
                        fontSize: titleFontSize,
                      ),
                    ),
                    if (subtitle != null)
                      Text(
                        subtitle!,
                        maxLines: 1,
                        overflow: TextOverflow.ellipsis,
                        style: subtitleBase?.copyWith(
                          color: textOnBlue.withOpacity(0.8),
                          fontWeight: FontWeight.w500, // Medium
                          fontSize: subtitleFontSize,
                        ),
                      ),
                  ],
                ),
              ),

              // Live Backend Connection Status Indicator
              ValueListenableBuilder<bool>(
                valueListenable: ApiConfig.isConnectedNotifier,
                builder: (context, isConnected, _) {
                  return InkWell(
                    onTap: () => _showConnectionDialog(context),
                    borderRadius: BorderRadius.circular(16),
                    child: Container(
                      padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                      margin: const EdgeInsets.only(right: 6),
                      decoration: BoxDecoration(
                        color: isConnected ? const Color(0xFF1B5E20) : const Color(0xFFB71C1C),
                        borderRadius: BorderRadius.circular(16),
                        border: Border.all(color: Colors.white24),
                      ),
                      child: Row(
                        mainAxisSize: MainAxisSize.min,
                        children: [
                          Icon(
                            isConnected ? Icons.cloud_done : Icons.cloud_off,
                            color: Colors.white,
                            size: statusIconSize,
                          ),
                          // On very small phones show only the icon to save space
                          if (!isCompact) ...[
                            const SizedBox(width: 4),
                            Text(
                              isConnected ? "CONNECTED" : "DISCONNECTED",
                              style: TextStyle(
                                color: Colors.white,
                                fontSize: statusFontSize,
                                fontWeight: FontWeight.bold,
                              ),
                            ),
                          ],
                        ],
                      ),
                    ),
                  );
                },
              ),

              // Notifications Button
              if (showNotifications)
                IconButton(
                  icon: const Icon(Icons.notifications),
                  iconSize: iconSize,
                  color: textOnBlue,
                  onPressed: onNotifications,
                ),

              // Avatar Button
              if (showAvatar)
                Padding(
                  padding: const EdgeInsets.only(right: 8.0),
                  child: Material(
                    shape: const CircleBorder(), // Modifier.clip(CircleShape)
                    color: blueMedium, // Modifier.background(BlueMedium)
                    clipBehavior: Clip.antiAlias,
                    child: InkWell(
                      onTap: onAvatar ?? () => _showConnectionDialog(context),
                      child: SizedBox(
                        width: avatarSize,
                        height: avatarSize,
                        child: Center(
                          child: Text(
                            avatarInitials,
                            style: Theme.of(context).textTheme.labelLarge?.copyWith(
                              color: textOnBlue,
                              fontWeight: FontWeight.bold,
                              fontSize: (Theme.of(context).textTheme.labelLarge?.fontSize ?? 14.0) * scale,
                            ),
                          ),
                        ),
                      ),
                    ),
                  ),
                ),
            ],
          ),
        ),
      ),
    );
  }

  static void _showConnectionDialog(BuildContext context) {
    final controller = TextEditingController(text: ApiConfig.baseUrl);
    bool testing = false;
    String? statusMsg;

    showDialog(
      context: context,
      builder: (ctx) {
        // ── MediaQuery values for the dialog ────────────────────────────
        final double dialogWidth = MediaQuery.sizeOf(ctx).width;
        final double dScale = (dialogWidth / 375).clamp(0.85, 1.2);
        final double dialogSideInset = (dialogWidth * 0.06).clamp(16.0, 40.0);

        return StatefulBuilder(
          builder: (ctx, setState) => AlertDialog(
            insetPadding: EdgeInsets.symmetric(
              horizontal: dialogSideInset,
              vertical: 24.0,
            ),
            scrollable: true, // keeps it usable with keyboard / landscape
            title: Row(
              children: [
                Icon(Icons.settings_ethernet, color: const Color(0xFF1565C0), size: 24.0 * dScale),
                const SizedBox(width: 8),
                const Expanded(
                  child: Text("Mandi Backend LAN Setup"),
                ),
              ],
            ),
            content: ConstrainedBox(
              constraints: const BoxConstraints(maxWidth: 480),
              child: Column(
                mainAxisSize: MainAxisSize.min,
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    "Configure PC FastAPI service address for phone-to-PC inspection sync over Wi-Fi:",
                    style: TextStyle(fontSize: 13 * dScale, color: const Color(0xFF64748B)),
                  ),
                  const SizedBox(height: 12),
                  TextField(
                    controller: controller,
                    decoration: const InputDecoration(
                      labelText: "API Base URL",
                      hintText: "http://192.168.x.x:8000",
                      border: OutlineInputBorder(),
                      isDense: true,
                    ),
                  ),
                  const SizedBox(height: 8),
                  if (statusMsg != null)
                    Padding(
                      padding: const EdgeInsets.only(top: 4.0),
                      child: Text(
                        statusMsg!,
                        style: TextStyle(
                          fontSize: 12 * dScale,
                          fontWeight: FontWeight.bold,
                          color: statusMsg!.startsWith("Connected") ? Colors.green : Colors.red,
                        ),
                      ),
                    ),
                  if (testing)
                    const Padding(
                      padding: EdgeInsets.only(top: 8.0),
                      child: Center(child: LinearProgressIndicator()),
                    ),
                ],
              ),
            ),
            actions: [
              TextButton(
                onPressed: testing
                    ? null
                    : () async {
                  setState(() {
                    testing = true;
                    statusMsg = null;
                  });
                  ApiConfig.setBaseUrl(controller.text);
                  final ok = await ApiConfig.checkConnection();
                  setState(() {
                    testing = false;
                    statusMsg = ok
                        ? "Connected! (Mandi Nyaay Core Active)"
                        : "Failed: ${ApiConfig.lastErrorNotifier.value ?? 'Unreachable'}";
                  });
                },
                child: const Text("TEST CONNECTION"),
              ),
              ElevatedButton(
                onPressed: () {
                  ApiConfig.setBaseUrl(controller.text);
                  Navigator.of(ctx).pop();
                },
                style: ElevatedButton.styleFrom(
                  backgroundColor: const Color(0xFF1565C0),
                  foregroundColor: Colors.white,
                ),
                child: const Text("SAVE & CLOSE"),
              ),
            ],
          ),
        );
      },
    );
  }
}