EC14 (USB-1408FS-Plus) – 64-bit Windows Port

Overview

This is a 64-bit Windows WPF application skeleton that replicates the EC14 TestPoint app’s functionality for the USB-1408FS-Plus DAQ:
- 4-channel analog scan using MCC Universal Library (UL) background + continuous mode
- 1XY and 2XY-1SC display modes (UI scaffolding ready)
- Footswitch handling via counter input (debounce/double-press logic placeholder)
- SPI bit-bang over digital port for AD9833 oscillators and LTC6912 gains (Mode C per the TestPoint report, data on bit 7, clock on bit 6, CS lines on bits 0..5)
- Save data/image and color/config persistence placeholders

Tech stack

- .NET 8, WPF, x64
- Direct P/Invoke to MCC UL `cbw64.dll` (no dependency on legacy 32-bit TestPoint DLLs)

Hardware and signal notes (from EC316K printout)

- Device: Measurement Computing USB-1408FS-Plus
- Scan: 4 interleaved channels (Ch0..Ch3), ring buffer; data then separated by decimation by 4
- Default if no config found: 12 kHz (Ch1) / 3 kHz (Ch2) differential/cross-axial
- Erase modes: Continuous, Block, Fixed (moving dot for XY)
- Footswitch: Uses counter input; reject unintentional double presses
- SPI: AD9833 frequency synth and LTC6912 gain via bit-bang
  - Chip select mapping (CS):
    - CS=0: FREQ 1 QUAD PHASE AD9833
    - CS=1: FREQ 1 IN-PHASE AD9833
    - CS=2: FREQ 2 IN-PHASE AD9833
    - CS=3: FREQ 2 QUAD PHASE AD9833
    - CS=4: FREQ 2 GAIN LTC6912
    - CS=5: FREQ 1 GAIN LTC6912
  - Mode: “Mode C” (per report). Data output on bit 7, CLK on bit 6, CS lines active low on bits 0..5

Prerequisites (on the 64-bit Windows target PC)

1) Install Measurement Computing InstaCal + Universal Library (UL) for Windows. Ensure 64-bit UL is installed (cbw64.dll).
2) Connect and configure the USB-1408FS-Plus in InstaCal (board number 0 by default).
3) Ensure `cbw64.dll` is in the system path (e.g., C:\Windows\System32) or copy it next to the app executable.
4) If you are using AD9833/LTC6912, wire the digital IO as follows:
   - Port used: 8-bit digital port. Bit 7 = Data (DOUT), Bit 6 = Clock (CLK), Bits 0..5 = CS0..CS5 (active-low)

Build and run

1) Open `NewFieldSystem/EC14.Wpf/EC14.Wpf.csproj` in Visual Studio 2022 (or open the folder and select the project).
2) Set configuration to x64.
3) Build and run. On first run without config, defaults are applied.

Notes on completeness

- This is a faithful port scaffold. The DAQ loop, background scan, cbWinBufAlloc/ToArray, cbGetStatus, cbStopBackground, digital I/O, counter input, and SPI sequencing are implemented/stubbed as per the report.
- Charting is minimal in this commit to keep dependencies light. You can plug in ScottPlot or LiveCharts2 for high-performance visuals.
- Image capture uses WPF rendering (replaces SnagIt COM automation in TestPoint).
- Color/config persistence placeholders are provided; adapt to exact `last.cfg`/`mycolors.cfg` formats as needed.

Troubleshooting

- If scans do not start, verify InstaCal recognizes the device and that `cbw64.dll` is discoverable.
- If SPI devices don’t respond, verify wiring and that CS lines idle high and go low only for the selected device.
- If footswitch events misfire, adjust debounce/double-press thresholds in `FootswitchService`.

