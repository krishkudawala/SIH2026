import 'package:flutter/material.dart';
import 'package:sih2631/manid_nyaay/data/api/api_config.dart';

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

  // Implements PreferredSizeWidget so you can use it in Scaffold(appBar: ...)
  @override
  Size get preferredSize => const Size.fromHeight(64.0);

  @override
  Widget build(BuildContext context) {
    // Material perfectly replicates Compose's Surface
    return Material(
      color: blueDark,
      elevation: 4.0, // shadowElevation
      child: SafeArea(
        bottom: false, // Replicates statusBarsPadding()
        child: Container(
          height: 64.0,
          padding: const EdgeInsets.symmetric(horizontal: 8.0),
          child: Row(
            crossAxisAlignment: CrossAxisAlignment.center, // verticalAlignment = Alignment.CenterVertically
            children: [
              // Back Button or Spacer
              if (showBack)
                IconButton(
                  icon: const Icon(Icons.arrow_back), // Auto-mirrored natively in Flutter
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
                      style: Theme.of(context).textTheme.titleLarge?.copyWith(
                        color: textOnBlue,
                        fontWeight: FontWeight.w800, // ExtraBold
                        letterSpacing: -0.5,
                      ),
                    ),
                    if (subtitle != null)
                      Text(
                        subtitle!,
                        style: Theme.of(context).textTheme.labelSmall?.copyWith(
                          color: textOnBlue.withOpacity(0.8),
                          fontWeight: FontWeight.w500, // Medium
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
                            size: 14,
                          ),
                          const SizedBox(width: 4),
                          Text(
                            isConnected ? "CONNECTED" : "DISCONNECTED",
                            style: const TextStyle(
                              color: Colors.white,
                              fontSize: 10,
                              fontWeight: FontWeight.bold,
                            ),
                          ),
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
                        width: 36.0,
                        height: 36.0,
                        child: Center(
                          child: Text(
                            avatarInitials,
                            style: Theme.of(context).textTheme.labelLarge?.copyWith(
                              color: textOnBlue,
                              fontWeight: FontWeight.bold,
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
      builder: (ctx) => StatefulBuilder(
        builder: (ctx, setState) => AlertDialog(
          title: const Row(
            children: [
              Icon(Icons.settings_ethernet, color: Color(0xFF1565C0)),
              SizedBox(width: 8),
              Text("Mandi Backend LAN Setup"),
            ],
          ),
          content: Column(
            mainAxisSize: MainAxisSize.min,
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              const Text(
                "Configure PC FastAPI service address for phone-to-PC inspection sync over Wi-Fi:",
                style: TextStyle(fontSize: 13, color: Color(0xFF64748B)),
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
                      fontSize: 12,
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
      ),
    );
  }
}