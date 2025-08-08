using System;

namespace EC14.Wpf.Services;

public sealed class FootswitchService
{
    private readonly DaqService _daq;
    private readonly int _counterNum;
    private uint _lastCount;
    private DateTime _lastEventUtc = DateTime.MinValue;

    public TimeSpan Debounce { get; set; } = TimeSpan.FromMilliseconds(150);
    public TimeSpan DoublePressReject { get; set; } = TimeSpan.FromMilliseconds(400);

    public FootswitchService(DaqService daq, int counterNum = 0)
    {
        _daq = daq;
        _counterNum = counterNum;
        _lastCount = _daq.CounterIn32(_counterNum);
    }

    public bool CheckTriggered()
    {
        uint count = _daq.CounterIn32(_counterNum);
        if (count != _lastCount)
        {
            _lastCount = count;
            var now = DateTime.UtcNow;
            if (now - _lastEventUtc < Debounce) return false;
            if (now - _lastEventUtc < DoublePressReject) return false; // reject rapid/double presses
            _lastEventUtc = now;
            return true;
        }
        return false;
    }
}

