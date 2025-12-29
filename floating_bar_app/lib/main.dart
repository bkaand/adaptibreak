import 'package:flutter/material.dart';
import 'package:window_manager/window_manager.dart';
import 'package:http/http.dart' as http;
import 'dart:async';
import 'dart:convert';

void main() async {
  WidgetsFlutterBinding.ensureInitialized();
  await windowManager.ensureInitialized();

  // Configure as a small horizontal floating bar
  WindowOptions windowOptions = const WindowOptions(
    size: Size(400, 50),
    center: false,
    backgroundColor: Colors.transparent,
    skipTaskbar: true,
    titleBarStyle: TitleBarStyle.hidden,
    alwaysOnTop: true,
  );

  windowManager.waitUntilReadyToShow(windowOptions, () async {
    await windowManager.show();
    await windowManager.setAsFrameless();
    await windowManager.setAlwaysOnTop(true);
    // Position at top center of screen
    await windowManager.setPosition(const Offset(500, 30));
  });

  runApp(const FloatingBarApp());
}

class FloatingBarApp extends StatelessWidget {
  const FloatingBarApp({Key? key}) : super(key: key);

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'AdaptiBreak Bar',
      debugShowCheckedModeBanner: false,
      theme: ThemeData(
        useMaterial3: true,
        colorScheme: ColorScheme.fromSeed(
          seedColor: const Color(0xFF6366F1),
          brightness: Brightness.dark,
        ),
      ),
      home: const FloatingBar(),
    );
  }
}

class FloatingBar extends StatefulWidget {
  const FloatingBar({Key? key}) : super(key: key);

  @override
  State<FloatingBar> createState() => _FloatingBarState();
}

class _FloatingBarState extends State<FloatingBar> with TickerProviderStateMixin {
  static const String apiUrl = 'http://127.0.0.1:8000';
  
  double fatigueScore = 0.0;
  int blinkCount = 0;
  int yawnCount = 0;
  double sessionDuration = 0.0;
  bool isConnected = false;
  bool isCalibrating = false;
  double calibrationProgress = 0.0;
  bool breakSuggested = false;
  
  Timer? statusTimer;
  Offset position = Offset.zero;
  
  late AnimationController _pulseController;

  @override
  void initState() {
    super.initState();
    
    _pulseController = AnimationController(
      duration: const Duration(milliseconds: 800),
      vsync: this,
    )..repeat(reverse: true);
    
    startPolling();
  }

  @override
  void dispose() {
    statusTimer?.cancel();
    _pulseController.dispose();
    super.dispose();
  }

  void startPolling() {
    statusTimer = Timer.periodic(const Duration(milliseconds: 500), (timer) {
      updateStatus();
    });
  }

  Future<void> updateStatus() async {
    try {
      final response = await http
          .get(Uri.parse('$apiUrl/status'))
          .timeout(const Duration(seconds: 1));

      if (response.statusCode == 200) {
        final data = json.decode(response.body);
        setState(() {
          fatigueScore = (data['score'] as num?)?.toDouble() ?? 0.0;
          blinkCount = (data['blink_rate'] as num?)?.toInt() ?? 0;
          yawnCount = (data['yawn_count'] as num?)?.toInt() ?? 0;
          sessionDuration = (data['session_duration'] as num?)?.toDouble() ?? 0.0;
          isCalibrating = data['is_calibrating'] ?? false;
          calibrationProgress = (data['calibration_progress'] as num?)?.toDouble() ?? 0.0;
          isConnected = sessionDuration > 0;
        });
      }
      
      // Check break status
      final breakResponse = await http
          .get(Uri.parse('$apiUrl/break_status'))
          .timeout(const Duration(seconds: 1));
      
      if (breakResponse.statusCode == 200) {
        final breakData = json.decode(breakResponse.body);
        setState(() {
          breakSuggested = breakData['break_suggested'] ?? false;
        });
      }
    } catch (e) {
      setState(() {
        isConnected = false;
      });
    }
  }

  Future<void> takeBreak() async {
    try {
      await http.post(Uri.parse('$apiUrl/acknowledge_break'));
      setState(() {
        breakSuggested = false;
      });
    } catch (e) {}
  }

  Future<void> stopSession() async {
    try {
      await http.post(Uri.parse('$apiUrl/stop'));
      windowManager.close();
    } catch (e) {}
  }

  Color getBarColor() {
    // Only red when break is suggested, otherwise stay grey (non-distracting)
    if (breakSuggested) return const Color(0xFFDC2626);
    return const Color(0xFF374151); // Neutral grey
  }

  String formatDuration(double seconds) {
    int mins = (seconds / 60).floor();
    int secs = (seconds % 60).floor();
    return '${mins.toString().padLeft(2, '0')}:${secs.toString().padLeft(2, '0')}';
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: Colors.transparent,
      body: MouseRegion(
        cursor: SystemMouseCursors.grab,
        child: GestureDetector(
          onPanStart: (details) async {
            position = await windowManager.getPosition();
          },
          onPanUpdate: (details) async {
            final newPos = Offset(
              position.dx + details.delta.dx,
              position.dy + details.delta.dy,
            );
            position = newPos;
            await windowManager.setPosition(newPos);
          },
          child: AnimatedContainer(
            duration: const Duration(milliseconds: 300),
            margin: const EdgeInsets.all(4),
            height: 42,
            decoration: BoxDecoration(
              gradient: LinearGradient(
                colors: [
                  getBarColor().withOpacity(0.95),
                  getBarColor().withOpacity(0.85),
                ],
              ),
              borderRadius: BorderRadius.circular(21),
              boxShadow: [
                BoxShadow(
                  color: getBarColor().withOpacity(0.4),
                  blurRadius: 12,
                  offset: const Offset(0, 4),
                ),
              ],
            ),
            child: Padding(
              padding: const EdgeInsets.symmetric(horizontal: 12),
              child: Row(
                mainAxisSize: MainAxisSize.min,
                children: [
                  // Status dot
                  AnimatedBuilder(
                    animation: _pulseController,
                    builder: (context, child) {
                      return Container(
                        width: 8,
                        height: 8,
                        decoration: BoxDecoration(
                          color: Colors.white.withOpacity(
                            isConnected ? 0.7 + (_pulseController.value * 0.3) : 0.3
                          ),
                          shape: BoxShape.circle,
                        ),
                      );
                    },
                  ),
                  
                  const SizedBox(width: 10),
                  
                  // Calibrating or fatigue info
                  if (isCalibrating) ...[
                    Text(
                      'Calibrating ${(calibrationProgress * 100).toInt()}%',
                      style: const TextStyle(
                        color: Colors.white,
                        fontSize: 12,
                        fontWeight: FontWeight.w500,
                      ),
                    ),
                  ] else if (isConnected) ...[
                    // Fatigue score
                    Text(
                      '${(fatigueScore * 100).toInt()}%',
                      style: const TextStyle(
                        color: Colors.white,
                        fontSize: 14,
                        fontWeight: FontWeight.bold,
                      ),
                    ),
                    
                    const SizedBox(width: 12),
                    
                    // Divider
                    Container(width: 1, height: 16, color: Colors.white24),
                    
                    const SizedBox(width: 12),
                    
                    // Duration
                    Row(
                      mainAxisSize: MainAxisSize.min,
                      children: [
                        Icon(Icons.timer, size: 12, color: Colors.white.withOpacity(0.7)),
                        const SizedBox(width: 4),
                        Text(
                          formatDuration(sessionDuration),
                          style: TextStyle(
                            color: Colors.white.withOpacity(0.9),
                            fontSize: 12,
                            fontWeight: FontWeight.w500,
                          ),
                        ),
                      ],
                    ),
                    
                    const SizedBox(width: 12),
                    
                    // Yawns
                    Row(
                      mainAxisSize: MainAxisSize.min,
                      children: [
                        Icon(Icons.face, size: 12, color: Colors.white.withOpacity(0.6)),
                        const SizedBox(width: 3),
                        Text(
                          '$yawnCount',
                          style: TextStyle(
                            color: Colors.white.withOpacity(0.9),
                            fontSize: 12,
                          ),
                        ),
                      ],
                    ),
                  ] else ...[
                    Text(
                      'Not Connected',
                      style: TextStyle(
                        color: Colors.white.withOpacity(0.6),
                        fontSize: 12,
                      ),
                    ),
                  ],
                  
                  const Spacer(),
                  
                  // Break button (if suggested)
                  if (breakSuggested) ...[
                    GestureDetector(
                      onTap: takeBreak,
                      child: MouseRegion(
                        cursor: SystemMouseCursors.click,
                        child: Container(
                          padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
                          decoration: BoxDecoration(
                            color: Colors.white,
                            borderRadius: BorderRadius.circular(12),
                          ),
                          child: const Text(
                            'Take Break',
                            style: TextStyle(
                              color: Color(0xFFDC2626),
                              fontSize: 11,
                              fontWeight: FontWeight.bold,
                            ),
                          ),
                        ),
                      ),
                    ),
                    const SizedBox(width: 8),
                  ],
                  
                  // Stop button
                  GestureDetector(
                    onTap: stopSession,
                    child: MouseRegion(
                      cursor: SystemMouseCursors.click,
                      child: Container(
                        padding: const EdgeInsets.all(6),
                        decoration: BoxDecoration(
                          color: Colors.white.withOpacity(0.15),
                          borderRadius: BorderRadius.circular(8),
                        ),
                        child: Icon(
                          Icons.stop,
                          size: 14,
                          color: Colors.white.withOpacity(0.8),
                        ),
                      ),
                    ),
                  ),
                  
                  const SizedBox(width: 6),
                  
                  // Close button
                  GestureDetector(
                    onTap: () => windowManager.close(),
                    child: MouseRegion(
                      cursor: SystemMouseCursors.click,
                      child: Icon(
                        Icons.close,
                        size: 14,
                        color: Colors.white.withOpacity(0.5),
                      ),
                    ),
                  ),
                ],
              ),
            ),
          ),
        ),
      ),
    );
  }
}
