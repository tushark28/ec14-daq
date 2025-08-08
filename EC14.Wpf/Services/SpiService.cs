using System;
using System.Threading;

namespace EC14.Wpf.Services;

public sealed class SpiService
{
    private readonly DaqService _daq;

    // Port/bit mapping per report: DOUT=bit7, CLK=bit6, CS0..CS5=bits 0..5 (active low)
    private const int PortNum = UlConstants.FIRSTPORTB; // matches report: Port B used for SPI
    private const int BitData = 7;
    private const int BitClk = 6;

    public SpiService(DaqService daq)
    {
        _daq = daq;
        // Configure port as output (1 = output for UL)
        _daq.DigitalConfigPort(PortNum, 1);
        // Idle states: CLK=1, DOUT=1, CSx=1 (inactive)
        _daq.DigitalOut(PortNum, (1 << BitData) | (1 << BitClk) | 0x3F);
    }

    public void SelectDevice(int csIndex)
    {
        // Active low: drive the corresponding CS bit to 0, others 1
        int mask = 0x3F; // bits 0..5 high
        mask &= ~(1 << csIndex);
        int value = (1 << BitData) | (1 << BitClk) | mask;
        _daq.DigitalOut(PortNum, value);
        SmallDelay();
    }

    public void DeselectAll()
    {
        int value = (1 << BitData) | (1 << BitClk) | 0x3F; // CS high
        _daq.DigitalOut(PortNum, value);
        SmallDelay();
    }

    // Mode C (clock idle high, sample on falling edge per report text)
    public void WriteBytes(ReadOnlySpan<byte> bytes)
    {
        foreach (byte b in bytes)
        {
            for (int i = 7; i >= 0; i--)
            {
                int bit = (b >> i) & 1;
                // Set data bit
                _daq.DigitalBitOut(PortNum, BitData, bit);
                SmallDelay();
                // Toggle clock high->low->high; data latched on high->low
                _daq.DigitalBitOut(PortNum, BitClk, 0);
                SmallDelay();
                _daq.DigitalBitOut(PortNum, BitClk, 1);
                SmallDelay();
            }
        }
    }

    private static void SmallDelay()
    {
        // Simple short delay; adjust as needed for device timing
        Thread.SpinWait(50);
    }
}

