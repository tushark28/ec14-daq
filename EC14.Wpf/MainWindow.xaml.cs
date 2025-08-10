using System;
using System.Threading;
using System.Threading.Tasks;
using System.Windows;
using System.Windows.Controls;

namespace EC14.Wpf;

public partial class MainWindow : Window
{
    private readonly Services.DaqService _daqService;
    private readonly Services.SpiService _spiService;
    private readonly Services.FootswitchService _footswitchService;

    private CancellationTokenSource? _runCts;

    public MainWindow()
    {
        InitializeComponent();
        _daqService = new Services.DaqService();
        _spiService = new Services.SpiService(_daqService);
        _footswitchService = new Services.FootswitchService(_daqService);
        _daqService.OnSamples += (_, _, _, _) =>
        {
            // Placeholder for refreshing charts
        };
        
        // Initialize digital ports for EC14 (per TestPoint report)
        try
        {
            _daqService.InitializeDigitalPortsForEc14();
            StatusText.Text = "Ready - Digital ports initialized";
        }
        catch (Exception ex)
        {
            StatusText.Text = $"Init error: {ex.Message}";
        }
    }

    private async void Run_Click(object sender, RoutedEventArgs e)
    {
        if (_runCts != null) return;
        _runCts = new CancellationTokenSource();
        SetUiEnabled(false);
        StatusText.Text = "Running";
        try
        {
            await _daqService.StartScanAsync(_runCts.Token);
        }
        catch (Exception ex)
        {
            StatusText.Text = ex.Message;
            SetUiEnabled(true);
            _runCts?.Cancel();
            _runCts = null;
        }
    }

    private void Stop_Click(object sender, RoutedEventArgs e)
    {
        _runCts?.Cancel();
        _runCts = null;
        _daqService.StopScan();
        StatusText.Text = "Ready";
        SetUiEnabled(true);
    }

    private void Balance_Click(object sender, RoutedEventArgs e)
    {
        // Placeholder: acquire ~1000 samples and compute averages to center strip chart
    }

    private void Offsets_Click(object sender, RoutedEventArgs e)
    {
        // Placeholder: open offsets dialog
    }

    private void SaveData_Click(object sender, RoutedEventArgs e)
    {
        // Placeholder: compute filename using Zone/Row/Tube; save buffers
    }

    private void SaveImage_Click(object sender, RoutedEventArgs e)
    {
        // Placeholder: render main window to PNG in Image Directory
    }

    private void Open1XYSetup_Click(object sender, RoutedEventArgs e)
    {
        // Placeholder: open 1XY Setup window
    }

    private void Open2XY1SCSetup_Click(object sender, RoutedEventArgs e)
    {
        // Placeholder: open 2XY-1SC Setup window
    }

    private void SaveSettings_Click(object sender, RoutedEventArgs e)
    {
        // Placeholder: persist last.cfg and mycolors.cfg equivalents
    }

    private void Exit_Click(object sender, RoutedEventArgs e)
    {
        Application.Current.Shutdown();
    }

    private void SetUiEnabled(bool enabled)
    {
        foreach (var child in ((Panel)Content).Children)
        {
            if (child is Panel p)
            {
                foreach (var c in p.Children)
                {
                    if (c is Button b)
                    {
                        b.IsEnabled = enabled;
                    }
                }
            }
        }
    }
}

