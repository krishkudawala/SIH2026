import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:sih2631/manid_nyaay/data/api/api_client.dart';
import 'package:sih2631/manid_nyaay/data/ui/components/mandi_app_bar.dart';

const Color backgroundGray = Color(0xFFF4F5F7);
const Color surfaceWhite = Colors.white;
const Color institutionalBlue = Color(0xFF1565C0);
const Color textPrimary = Color(0xFF1E293B);
const Color textSecondary = Color(0xFF64748B);
const Color textOnBlue = Colors.white;
const Color dividerGray = Color(0xFFE2E8F0);

const Color gradeAColor = Color(0xFF4CAF50);
const Color ursColor = Color(0xFFFFA000);
const Color rejectColor = Color(0xFFEF4444);

class ReportsScreen extends StatefulWidget {
  const ReportsScreen({super.key});

  @override
  State<ReportsScreen> createState() => _ReportsScreenState();
}

class _ReportsScreenState extends State<ReportsScreen> {
  final MandiApiClient _api = MandiApiClient();
  bool _isLoading = true;
  String? _errorMessage;
  List<Map<String, dynamic>> _sessions = [];

  int _totalLots = 0;
  int _gradeACount = 0;
  int _ursCount = 0;
  int _rejectCount = 0;
  int _otherCount = 0;

  @override
  void initState() {
    super.initState();
    _loadReportData();
  }

  Future<void> _loadReportData() async {
    setState(() {
      _isLoading = true;
      _errorMessage = null;
    });

    try {
      final raw = await _api.listSessions(limit: 100);
      final sessions = raw.map((e) => Map<String, dynamic>.from(e as Map)).toList();

      int a = 0, u = 0, r = 0, o = 0;
      for (final s in sessions) {
        final grade = (s['procurement_grade'] ?? '').toString().toUpperCase();
        if (grade == 'GRADE_A') {
          a++;
        } else if (grade == 'URS' || grade == 'GRADE_B') {
          u++;
        } else if (grade == 'REJECT' || grade == 'GRADE_C') {
          r++;
        } else {
          o++;
        }
      }

      if (mounted) {
        setState(() {
          _sessions = sessions;
          _totalLots = sessions.length;
          _gradeACount = a;
          _ursCount = u;
          _rejectCount = r;
          _otherCount = o;
          _isLoading = false;
        });
      }
    } catch (e) {
      if (mounted) {
        setState(() {
          _errorMessage = "Unable to connect to Mandi backend for reports: $e";
          _isLoading = false;
        });
      }
    }
  }

  void _viewSessionReport(String sessionId) async {
    showDialog(
      context: context,
      barrierDismissible: false,
      builder: (ctx) => const Center(child: CircularProgressIndicator()),
    );

    try {
      final report = await _api.getReport(sessionId);
      if (mounted) Navigator.of(context).pop();

      final text = (report['printable_receipt'] ?? report['markdown_report'] ?? report['receipt_text'] ?? 'No text available').toString();

      if (mounted) {
        showDialog(
          context: context,
          builder: (ctx) => AlertDialog(
            title: Text("Audit Report ($sessionId)"),
            content: SingleChildScrollView(
              child: SelectableText(
                text,
                style: const TextStyle(fontFamily: 'monospace', fontSize: 12),
              ),
            ),
            actions: [
              TextButton(
                onPressed: () {
                  Clipboard.setData(ClipboardData(text: text));
                  ScaffoldMessenger.of(context).showSnackBar(
                    const SnackBar(content: Text("Copied report to clipboard")),
                  );
                },
                child: const Text("COPY"),
              ),
              ElevatedButton(
                onPressed: () => Navigator.of(ctx).pop(),
                child: const Text("CLOSE"),
              ),
            ],
          ),
        );
      }
    } catch (e) {
      if (mounted) {
        Navigator.of(context).pop();
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text("Error fetching report: $e")),
        );
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    final now = DateTime.now();
    final months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];
    final dateStr = "${months[now.month - 1]} ${now.day}, ${now.year}";

    final stats = [
      ("Total Lots", _totalLots, institutionalBlue),
      ("Grade A", _gradeACount, gradeAColor),
      ("Grade B / URS", _ursCount, ursColor),
      ("Grade C / Reject", _rejectCount, rejectColor),
      ("In Progress / Review", _otherCount, textSecondary),
    ];

    return Scaffold(
      backgroundColor: backgroundGray,
      appBar: MandiTopAppBar(
        title: "Statutory Reports",
        subtitle: "APMC Daily Audit Breakdown",
        showBack: false,
        onNotifications: _loadReportData,
      ),
      body: _isLoading
          ? const Center(child: CircularProgressIndicator())
          : _errorMessage != null
              ? Center(
                  child: Padding(
                    padding: const EdgeInsets.all(24.0),
                    child: Column(
                      mainAxisSize: MainAxisSize.min,
                      children: [
                        const Icon(Icons.cloud_off, size: 48, color: Colors.red),
                        const SizedBox(height: 12),
                        Text(
                          _errorMessage!,
                          textAlign: TextAlign.center,
                          style: const TextStyle(color: textPrimary),
                        ),
                        const SizedBox(height: 16),
                        ElevatedButton.icon(
                          onPressed: _loadReportData,
                          icon: const Icon(Icons.refresh),
                          label: const Text("Retry Connection"),
                        ),
                      ],
                    ),
                  ),
                )
              : SingleChildScrollView(
                  padding: const EdgeInsets.all(14.0),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      // Date Row
                      Card(
                        margin: EdgeInsets.zero,
                        elevation: 1.0,
                        color: surfaceWhite,
                        shape: RoundedRectangleBorder(
                          borderRadius: BorderRadius.circular(8.0),
                        ),
                        child: Padding(
                          padding: const EdgeInsets.all(12.0),
                          child: Row(
                            mainAxisAlignment: MainAxisAlignment.spaceBetween,
                            children: [
                              Row(
                                children: [
                                  const Icon(
                                    Icons.date_range,
                                    color: institutionalBlue,
                                    size: 18.0,
                                  ),
                                  const SizedBox(width: 8.0),
                                  Text(
                                    dateStr,
                                    style: Theme.of(context).textTheme.titleSmall?.copyWith(
                                      fontWeight: FontWeight.w600,
                                      color: textPrimary,
                                    ),
                                  ),
                                ],
                              ),
                              IconButton(
                                icon: const Icon(Icons.refresh, size: 18, color: institutionalBlue),
                                onPressed: _loadReportData,
                              ),
                            ],
                          ),
                        ),
                      ),
                      const SizedBox(height: 12.0),

                      // Summary Stats Card
                      Card(
                        margin: EdgeInsets.zero,
                        elevation: 1.0,
                        color: surfaceWhite,
                        shape: RoundedRectangleBorder(
                          borderRadius: BorderRadius.circular(8.0),
                        ),
                        child: Padding(
                          padding: const EdgeInsets.all(14.0),
                          child: Column(
                            crossAxisAlignment: CrossAxisAlignment.start,
                            children: [
                              Text(
                                "Live APMC Inspection Aggregates",
                                style: Theme.of(context).textTheme.titleSmall?.copyWith(
                                  fontWeight: FontWeight.w600,
                                  color: textPrimary,
                                ),
                              ),
                              const SizedBox(height: 10.0),

                              for (var i = 0; i < stats.length; i++) ...[
                                Padding(
                                  padding: const EdgeInsets.symmetric(vertical: 5.0),
                                  child: Row(
                                    children: [
                                      Container(
                                        width: 10.0,
                                        height: 10.0,
                                        decoration: BoxDecoration(
                                          color: stats[i].$3,
                                          shape: BoxShape.circle,
                                        ),
                                      ),
                                      const SizedBox(width: 10.0),
                                      Expanded(
                                        child: Text(
                                          stats[i].$1,
                                          style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                                            color: textPrimary,
                                          ),
                                        ),
                                      ),
                                      Text(
                                        stats[i].$2.toString(),
                                        style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                                          fontWeight: FontWeight.bold,
                                          color: stats[i].$3,
                                        ),
                                      ),
                                    ],
                                  ),
                                ),
                                if (i < stats.length - 1)
                                  const Divider(
                                    color: dividerGray,
                                    thickness: 0.5,
                                    height: 1.0,
                                  ),
                              ],
                            ],
                          ),
                        ),
                      ),
                      const SizedBox(height: 16.0),

                      // Recent Session Audit Reports
                      Text(
                        "Recent Session Audit Reports (${_sessions.length})",
                        style: Theme.of(context).textTheme.titleSmall?.copyWith(
                          fontWeight: FontWeight.bold,
                          color: textPrimary,
                        ),
                      ),
                      const SizedBox(height: 8.0),

                      if (_sessions.isEmpty)
                        const Card(
                          color: surfaceWhite,
                          child: Padding(
                            padding: EdgeInsets.all(16.0),
                            child: Text(
                              "No inspection reports committed yet. Complete an inspection to generate a statutory audit slip.",
                              style: TextStyle(fontSize: 12, color: textSecondary),
                            ),
                          ),
                        )
                      else
                        ListView.separated(
                          shrinkWrap: true,
                          physics: const NeverScrollableScrollPhysics(),
                          itemCount: _sessions.length.clamp(0, 10),
                          separatorBuilder: (context, index) => const SizedBox(height: 6.0),
                          itemBuilder: (context, index) {
                            final sess = _sessions[index];
                            final id = sess['id']?.toString() ?? '';
                            final lotId = sess['lot_id']?.toString() ?? '';
                            final grade = sess['procurement_grade']?.toString() ?? 'IN_PROGRESS';

                            return Card(
                              margin: EdgeInsets.zero,
                              elevation: 1.0,
                              color: surfaceWhite,
                              child: ListTile(
                                dense: true,
                                title: Text(
                                  "$lotId ($id)",
                                  style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 13),
                                ),
                                subtitle: Text("Grade: $grade • Status: ${sess['status']}"),
                                trailing: OutlinedButton(
                                  style: OutlinedButton.styleFrom(
                                    visualDensity: VisualDensity.compact,
                                  ),
                                  onPressed: () => _viewSessionReport(id),
                                  child: const Text("View Slip"),
                                ),
                              ),
                            );
                          },
                        ),
                    ],
                  ),
                ),
    );
  }
}