using System;
using System.Runtime.InteropServices;
using System.Threading;
using System.Threading.Tasks;

namespace EC14.Wpf.Services;

public sealed class DaqService
{
    // MCC UL constants (partial)
    private const int FunctionTypeAinScan = UlConstants.FT_AINSCAN;
    private const int OptionBackground = 1; // CONTINUOUS=2, BACKGROUND=1; TestPoint used 3 (both)
    private const int OptionContinuous = 2;

    private readonly object _lock = new();

    // Configurable
    public int BoardNum { get; init; } = 0;
    public int LowChannel { get; init; } = 0;
    public int HighChannel { get; init; } = 3;
    public int SampleRatePerChannel { get; set; } = 12000; // default per report
    public int AdRange { get; set; } = 0; // board default range index

    // Buffer state
    private int _numSamples = 1984; // 4*31*16 per report
    private IntPtr _dataHandle = IntPtr.Zero;
    private int _markIndex;

    // Status
    private volatile bool _running;

    public event Action<double[]?, double[]?, double[]?, double[]?>? OnSamples;

    public Task StartScanAsync(CancellationToken cancellationToken)
    {
        lock (_lock)
        {
            if (_running) return Task.CompletedTask;
            _running = true;
        }

        return Task.Run(() =>
        {
            try
            {
                // Allocate
                _dataHandle = Cbw.cbWinBufAlloc(_numSamples);
                if (_dataHandle == IntPtr.Zero)
                {
                    throw new InvalidOperationException("Windows Buffer BAD");
                }

                int count = _numSamples;
                int rate = SampleRatePerChannel;
                int options = OptionBackground | OptionContinuous; // 3

                int err = Cbw.cbAInScan(BoardNum, LowChannel, HighChannel, ref count, ref rate, AdRange, _dataHandle, options);
                if (err != 0)
                {
                    ThrowUlError(err, nameof(Cbw.cbAInScan));
                }

                _markIndex = 0;
                int status = 0, curCount = 0, curIndex = 0;
                while (!cancellationToken.IsCancellationRequested)
                {
                    err = Cbw.cbGetStatus(BoardNum, out status, out curCount, out curIndex, FunctionTypeAinScan);
                    if (err != 0)
                    {
                        ThrowUlError(err, nameof(Cbw.cbGetStatus));
                    }
                    if (status == 2) // RUNNING
                    {
                        if (curIndex != _markIndex)
                        {
                            int segmentLength = curIndex > _markIndex
                                ? curIndex - _markIndex
                                : (curCount > 0 ? curCount : _numSamples) - _markIndex + curIndex;

                            if (segmentLength > 0 && segmentLength <= _numSamples)
                            {
                                // Copy interleaved data into managed buffer
                                ushort[] interleaved = new ushort[segmentLength];
                                int firstPoint = _markIndex;
                                int copy1 = segmentLength;
                                if (curIndex < _markIndex)
                                {
                                    // Wrap: copy to end, then from start
                                    int endLen = (_numSamples - _markIndex);
                                    ushort[] temp = new ushort[endLen];
                                    err = Cbw.cbWinBufToArray(_dataHandle, temp, firstPoint, endLen);
                                    if (err != 0) ThrowUlError(err, nameof(Cbw.cbWinBufToArray));
                                    Array.Copy(temp, 0, interleaved, 0, endLen);
                                    int startLen = segmentLength - endLen;
                                    if (startLen > 0)
                                    {
                                        ushort[] temp2 = new ushort[startLen];
                                        err = Cbw.cbWinBufToArray(_dataHandle, temp2, 0, startLen);
                                        if (err != 0) ThrowUlError(err, nameof(Cbw.cbWinBufToArray));
                                        Array.Copy(temp2, 0, interleaved, endLen, startLen);
                                    }
                                }
                                else
                                {
                                    err = Cbw.cbWinBufToArray(_dataHandle, interleaved, firstPoint, copy1);
                                    if (err != 0) ThrowUlError(err, nameof(Cbw.cbWinBufToArray));
                                }

                                // Demux 4 channels by decimation
                                int samplesPerChannel = segmentLength / 4;
                                if (samplesPerChannel > 0)
                                {
                                    double[] ch0 = new double[samplesPerChannel];
                                    double[] ch1 = new double[samplesPerChannel];
                                    double[] ch2 = new double[samplesPerChannel];
                                    double[] ch3 = new double[samplesPerChannel];
                                    for (int i = 0; i < samplesPerChannel; i++)
                                    {
                                        int baseIdx = i * 4;
                                        ch0[i] = CodeToVolts(interleaved[baseIdx + 0]);
                                        ch1[i] = CodeToVolts(interleaved[baseIdx + 1]);
                                        ch2[i] = CodeToVolts(interleaved[baseIdx + 2]);
                                        ch3[i] = CodeToVolts(interleaved[baseIdx + 3]);
                                    }
                                    OnSamples?.Invoke(ch0, ch1, ch2, ch3);
                                }

                                _markIndex = curIndex;
                            }
                        }
                    }
                    Thread.Sleep(5);
                }
            }
            finally
            {
                StopScan();
            }
        }, cancellationToken);
    }

    public void StopScan()
    {
        lock (_lock)
        {
            if (!_running) return;
            _running = false;
        }
        try
        {
            // Stop background
            Cbw.cbStopBackground(BoardNum, FunctionTypeAinScan);
        }
        catch
        {
            // ignore
        }
        if (_dataHandle != IntPtr.Zero)
        {
            Cbw.cbWinBufFree(_dataHandle);
            _dataHandle = IntPtr.Zero;
        }
    }

    public int DigitalBitOut(int portNum, int bitNum, int bitValue)
    {
        return Cbw.cbDBitOut(BoardNum, portNum, bitNum, bitValue);
    }

    public int DigitalOut(int portNum, int value)
    {
        return Cbw.cbDOut(BoardNum, portNum, value);
    }

    public int DigitalConfigPort(int portNum, int direction)
    {
        return Cbw.cbDConfigPort(BoardNum, portNum, direction);
    }

    public void InitializeDigitalPortsForEc14()
    {
        // Per report: Port A output, set all lines high; Port B output, set lines 0,1 high, remainder low
        DigitalConfigPort(UlConstants.FIRSTPORTA, UlConstants.DIGITALOUT);
        DigitalOut(UlConstants.FIRSTPORTA, 0xFF);
        DigitalConfigPort(UlConstants.FIRSTPORTB, UlConstants.DIGITALOUT);
        DigitalOut(UlConstants.FIRSTPORTB, 0x07);
    }

    public uint CounterIn32(int counterNum)
    {
        int err = Cbw.cbCIn32(BoardNum, counterNum, out uint count);
        if (err != 0) ThrowUlError(err, nameof(Cbw.cbCIn32));
        return count;
    }

    private static void ThrowUlError(int errCode, string api)
    {
        var buffer = new System.Text.StringBuilder(256);
        Cbw.cbGetErrMsg(errCode, buffer, buffer.Capacity);
        string msg = buffer.ToString();
        throw new InvalidOperationException($"{api}: {msg} (err={errCode})");
    }

    private double CodeToVolts(ushort code)
    {
        // Use UL conversion for correctness
        float eng = 0;
        int err = Cbw.cbToEngUnits(BoardNum, AdRange, code, out eng);
        if (err != 0)
        {
            // Fallback: assume +/-5V, 14-bit resolution
            const double fullScale = 10.0; // -5..+5
            const double maxCode = 16383.0;
            double volts = (code / maxCode) * fullScale - 5.0;
            return volts;
        }
        return eng;
    }
}

internal static class Cbw
{
    private const string Dll = "cbw64.dll";

    [DllImport(Dll)]
    public static extern int cbAInScan(int boardNum, int lowChan, int highChan, ref int count, ref int rate, int range, IntPtr dataBuffer, int options);

    [DllImport(Dll)]
    public static extern IntPtr cbWinBufAlloc(int numPoints);

    [DllImport(Dll)]
    public static extern int cbWinBufFree(IntPtr memHandle);

    [DllImport(Dll)]
    public static extern int cbGetStatus(int boardNum, out int status, out int curCount, out int curIndex, int functionType);

    [DllImport(Dll)]
    public static extern int cbStopBackground(int boardNum, int functionType);

    [DllImport(Dll)]
    public static extern int cbDOut(int boardNum, int portNum, int value);

    [DllImport(Dll)]
    public static extern int cbDBitOut(int boardNum, int portNum, int bitNum, int bitValue);

    [DllImport(Dll)]
    public static extern int cbDConfigPort(int boardNum, int portNum, int direction);

    [DllImport(Dll)]
    public static extern int cbCIn32(int boardNum, int counterNum, out uint count);

    [DllImport(Dll, CharSet = CharSet.Ansi)]
    public static extern int cbGetErrMsg(int errCode, System.Text.StringBuilder errMsg, int maxLen);

    [DllImport(Dll)]
    public static extern int cbWinBufToArray(IntPtr memHandle, [Out] ushort[] userArray, int firstPoint, int count);

    [DllImport(Dll)]
    public static extern int cbToEngUnits(int boardNum, int range, ushort dataValue, out float engUnits);
}

