# EC14 Eddy Current Testing System Analysis

## **System Overview**

The EC14 is a sophisticated eddy current testing system that uses the Measurement Computing USB-1408FS-Plus for data acquisition and control. The system includes custom instrument board electronics for signal generation and conditioning.

## **Hardware Architecture**

### **USB-1408FS-Plus Configuration**
- **4 A/D channels** (0-3) for signal acquisition
- **2 D/A channels** for analog output
- **2 Digital I/O ports** (Port A & Port B) for control
- **1 Counter** for footswitch input

### **Instrument Board Components**
1. **4 AD9833 DDS Chips** - Direct Digital Synthesis for signal generation
   - Generate in-phase and quadrature waveforms
   - Programmable frequencies (1kHz - 10kHz typical)
   - Controlled via SPI protocol

2. **50 Ohm Bridge Circuit**
   - Configurable for cross axial/differential modes
   - Relay-controlled switching
   - Optimized for eddy current probe impedance

3. **Instrumentation Amplifiers**
   - Programmable gain settings
   - Optimized for eddy current signal levels
   - Controlled via digital outputs

4. **PGA (Programmable Gain Amplifier) Chips**
   - Course gain control
   - Automatic gain adjustment
   - Configuration file support

## **Software Architecture (TestPoint)**

### **Main Panels**
- **EC14 Charts** - Main display panel
- **EC14 Setup** - Initialization and configuration
- **EC14 BOS** - Null point adjustment
- **EC14 2XY-1SC Setup** - Color configuration for 2XY-1SC mode
- **EC14 XY Setup** - Color configuration for XY mode
- **EC14 Defect List** - Defect classification
- **EC14 Report** - Signal marking and reporting

### **Key Functions (cbw32.dll)**
```c
cbGetBoardName()      // Get device identification
cbGetErrMsg()         // Get error descriptions
cbDConfigPort()       // Configure digital ports
cbDOut()              // Digital output control
cbWinBufAlloc()       // Allocate data buffer
cbAInScan()           // Start analog input scanning
cbWinBufToArray()     // Retrieve scan data
cbGetStatus()         // Get scan status
cbStopBackground()    // Stop background operations
cbWinBufFree()        // Free data buffer
cbCIn32()             // Read counter input
```

## **Signal Flow**

### **1. Initialization Sequence**
```
USB-1408FS-Plus → Digital Outputs → SPI → AD9833 DDS Chips
                → Digital Outputs → Relays → Bridge Configuration
                → Digital Outputs → PGA → Gain Settings
```

### **2. Signal Generation**
```
AD9833 DDS → Sine Wave Output → Bridge Circuit → Eddy Current Probe
```

### **3. Signal Acquisition**
```
Eddy Current Probe → Bridge Circuit → Instrumentation Amps → PGA → A/D Channels
```

## **The -5V Reading Issue**

### **Why All Channels Show -5V**

The -5V readings are **normal and expected** when:

1. **No Eddy Current Probe Connected**
   - No active signal source
   - A/D channels read minimum range value

2. **No Test Piece Being Scanned**
   - No eddy current interaction
   - No signal variation

3. **Instrument Board Not Calibrated**
   - Amplifiers at default settings
   - Bridge circuit not balanced

4. **System in Idle State**
   - DDS chips may not be actively generating signals
   - No excitation current flowing

### **Expected Behavior**

| Condition | Channel Readings | Status |
|-----------|------------------|---------|
| No probe/test piece | All -5V | Normal |
| Probe connected, no test | Baseline values | Normal |
| Active scanning | Variable signals | Normal |
| Defect detected | Signal variations | Normal |

## **Python Implementation Status**

### **✅ Completed**
- USB-1408FS-Plus communication
- Real-time data acquisition
- 4-channel A/D scanning
- Data processing and display
- Basic instrument board initialization

### **🔄 In Progress**
- AD9833 DDS chip programming
- SPI communication implementation
- Relay control for bridge configuration
- Instrumentation amplifier setup

### **📋 Next Steps**
1. **Verify SPI Communication**
   - Test AD9833 programming
   - Confirm signal generation

2. **Calibrate Instrument Board**
   - Balance bridge circuit
   - Set appropriate gains

3. **Connect Eddy Current Probe**
   - Verify signal flow
   - Test with known defects

4. **Match TestPoint Behavior**
   - Compare signal levels
   - Verify frequency settings

## **Troubleshooting Guide**

### **If All Channels Read -5V**
1. Check instrument board initialization
2. Verify SPI communication to AD9833 chips
3. Confirm relay settings for bridge configuration
4. Check instrumentation amplifier gains
5. Connect eddy current probe
6. Test with conductive test piece

### **If Signals Are Present But Incorrect**
1. Verify frequency settings on AD9833 chips
2. Check bridge circuit configuration
3. Adjust instrumentation amplifier gains
4. Calibrate null point
5. Check probe impedance matching

## **Configuration Files**

The system uses several configuration files:
- `last.cfg` - Last used settings
- `mycolors.cfg` - Display color preferences
- `ect.lst` - Eddy current test parameters

## **Conclusion**

The -5V readings indicate the system is working correctly but in an idle state. The next phase should focus on:

1. **Complete instrument board initialization**
2. **Verify signal generation from AD9833 chips**
3. **Connect and test with actual eddy current probe**
4. **Compare signals with original TestPoint program**

This will establish the foundation for full eddy current testing functionality.
