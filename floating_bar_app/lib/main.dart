import 'package:flutter/material.dart';
import 'package:window_manager/window_manager.dart';
import 'package:http/http.dart' as http;
import 'dart:async';
import 'dart:convert';
import 'dart:ui';

void main() async {
  WidgetsFlutterBinding.ensureInitialized();
  await windowManager.ensureInitialized();

  // Configure floating window
  WindowOptions windowOptions = const WindowOptions(
    size: Size(240, 70),
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
    await windowManager.setPosition(const Offset(100, 100));
  });

  runApp(const FloatingBarApp());
}

class FloatingBarApp extends StatelessWidget {
  const FloatingBarApp({Key? key}) : super(key: key);

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'AdaptiBreak Monitor',
      debugShowCheckedModeBanner: false,
      theme: ThemeData(
        useMaterial3: true,
        colorScheme: ColorScheme.fromSeed(seedColor: Colors.blue),
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

class _FloatingBarState extends State<FloatingBar> with WindowListener {
  static const String apiUrl = 'http://127.0.0.1:8000';
  
  double fatigueScore = 0.0;
  bool isConnected = false;
  Timer? statusTimer;
  
  Offset position = Offset.zero;

  @override
  void initState() {
    super.initState();
    windowManager.addListener(this);
    startPolling();
  }

  @override
  void dispose() {
    windowManager.removeListener(this);
    statusTimer?.cancel();
    super.dispose();
  }

  void startPolling() {
    statusTimer = Timer.periodic(const Duration(seconds: 2), (timer) {
      updateStatus();
    });
  }

  Future<void> updateStatus() async {
    try {
      final response = await http
          .get(Uri.parse('$apiUrl/status'))
          .timeout(const Duration(seconds: 2));

      if (response.statusCode == 200) {
        final data = json.decode(response.body);
        setState(() {
          fatigueScore = (data['score'] as num).toDouble();
          isConnected = true;
        });
      }
    } catch (e) {
      setState(() {
        isConnected = false;
      });
    }
  }

  Color getFatigueColor() {
    if (!isConnected) return Colors.grey;
    if (fatigueScore > 0.6) return Colors.red;
    if (fatigueScore > 0.4) return Colors.orange;
    return Colors.green;
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
            await windowManager.setPosition(
              Offset(
                position.dx + details.delta.dx,
                position.dy + details.delta.dy,
              ),
            );
          },
          child: Container(
            margin: const EdgeInsets.all(4),
            decoration: BoxDecoration(
              color: const Color(0xFF2C3E50).withOpacity(0.95),
              borderRadius: BorderRadius.circular(25),
              boxShadow: [
                BoxShadow(
                  color: Colors.black.withOpacity(0.4),
                  blurRadius: 12,
                  offset: const Offset(0, 4),
                ),
              ],
            ),
            child: ClipRRect(
              borderRadius: BorderRadius.circular(25),
              child: BackdropFilter(
                filter: ImageFilter.blur(sigmaX: 10, sigmaY: 10),
                child: Padding(
                  padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 10),
                  child: Row(
                    mainAxisSize: MainAxisSize.min,
                    children: [
                      // Status indicator
                      Container(
                        width: 14,
                        height: 14,
                        decoration: BoxDecoration(
                          color: getFatigueColor(),
                          shape: BoxShape.circle,
                          boxShadow: [
                            BoxShadow(
                              color: getFatigueColor().withOpacity(0.5),
                              blurRadius: 4,
                              spreadRadius: 1,
                            ),
                          ],
                        ),
                      ),
                      
                      const SizedBox(width: 10),
                      
                      // Text content
                      Flexible(
                        child: Column(
                          mainAxisAlignment: MainAxisAlignment.center,
                          crossAxisAlignment: CrossAxisAlignment.start,
                          mainAxisSize: MainAxisSize.min,
                          children: [
                            Text(
                              isConnected ? 'Monitoring' : 'Not Connected',
                              style: const TextStyle(
                                color: Colors.white,
                                fontSize: 11,
                                fontWeight: FontWeight.w600,
                                letterSpacing: 0.3,
                              ),
                              maxLines: 1,
                              overflow: TextOverflow.ellipsis,
                            ),
                            const SizedBox(height: 2),
                            Text(
                              isConnected
                                  ? 'Fatigue: ${fatigueScore.toStringAsFixed(2)}'
                                  : 'Start backend',
                              style: TextStyle(
                                color: Colors.white.withOpacity(0.8),
                                fontSize: 9,
                              ),
                              maxLines: 1,
                              overflow: TextOverflow.ellipsis,
                            ),
                          ],
                        ),
                      ),
                      
                      const SizedBox(width: 8),
                      
                      // Close button
                      GestureDetector(
                        onTap: () {
                          windowManager.close();
                        },
                        child: MouseRegion(
                          cursor: SystemMouseCursors.click,
                          child: Container(
                            padding: const EdgeInsets.all(4),
                            child: Icon(
                              Icons.close,
                              size: 12,
                              color: Colors.white.withOpacity(0.7),
                            ),
                          ),
                        ),
                      ),
                    ],
                  ),
                ),
              ),
            ),
          ),
        ),
      ),
    );
  }
}

