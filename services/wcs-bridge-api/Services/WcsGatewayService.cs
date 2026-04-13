using Microsoft.Extensions.Options;
using TQG.Automation.SDK;
using TQG.Automation.SDK.Configuration;
using TQG.Automation.SDK.Events;
using TQG.Automation.SDK.Shared;
using WcsBridgeApi.Contracts;

namespace WcsBridgeApi.Services;

public sealed class WcsGatewayService
{
    private readonly AutomationGateway _gateway = AutomationGateway.Instance;
    private readonly GatewayEventStore _eventStore;
    private readonly WcsBridgeOptions _options;
    private readonly IHostEnvironment _environment;
    private readonly ILogger<WcsGatewayService> _logger;

    public WcsGatewayService(
        GatewayEventStore eventStore,
        IOptions<WcsBridgeOptions> options,
        IHostEnvironment environment,
        ILogger<WcsGatewayService> logger)
    {
        _eventStore = eventStore;
        _options = options.Value;
        _environment = environment;
        _logger = logger;

        SubscribeToEvents();
    }

    public bool IsInitialized => _gateway.IsInitialized;

    public int DeviceCount => _gateway.DeviceCount;

    public bool IsQueuePaused => _gateway.IsInitialized && _gateway.IsPauseQueue;

    public async Task TryAutoInitializeAsync(CancellationToken cancellationToken)
    {
        if (string.IsNullOrWhiteSpace(_options.GatewayConfigurationPath))
        {
            _logger.LogInformation("WCS bridge started without auto-initialize configuration.");
            return;
        }

        if (_gateway.IsInitialized)
        {
            return;
        }

        _logger.LogInformation("Auto-initializing gateway from configured startup files.");

        await InitializeAsync(new InitializeGatewayRequest
        {
            ActivateAllDevices = _options.ActivateAllDevicesOnStartup
        }, cancellationToken);
    }

    public async Task<GatewaySnapshotResponse> InitializeAsync(
        InitializeGatewayRequest request,
        CancellationToken cancellationToken)
    {
        if (_gateway.IsInitialized)
        {
            throw new InvalidOperationException(
                "AutomationGateway is already initialized. Restart this service before re-initializing with a new configuration.");
        }

        var configurationJson = await ResolveRequiredJsonAsync(
            request.ConfigurationJson,
            request.ConfigurationPath,
            _options.GatewayConfigurationPath,
            "gateway configuration",
            cancellationToken);

        _gateway.Initialize(configurationJson);

        var layoutJson = await ResolveOptionalJsonAsync(
            request.WarehouseLayoutJson,
            request.WarehouseLayoutPath,
            _options.WarehouseLayoutPath,
            cancellationToken);

        if (!string.IsNullOrWhiteSpace(layoutJson))
        {
            _gateway.LoadWarehouseLayout(layoutJson);
        }

        if (request.ActivateAllDevices || _options.ActivateAllDevicesOnStartup)
        {
            await _gateway.ActivateAllDevicesAsync(cancellationToken);
        }

        _eventStore.Add("gateway_initialized", null, null, new
        {
            deviceCount = _gateway.DeviceCount,
            deviceIds = _gateway.DeviceIds.OrderBy(id => id).ToArray()
        });

        return await GetSnapshotAsync(cancellationToken);
    }

    public async Task LoadWarehouseLayoutAsync(
        LoadWarehouseLayoutRequest request,
        CancellationToken cancellationToken)
    {
        EnsureInitialized();

        var layoutJson = await ResolveRequiredJsonAsync(
            request.LayoutJson,
            request.LayoutPath,
            _options.WarehouseLayoutPath,
            "warehouse layout",
            cancellationToken);

        _gateway.LoadWarehouseLayout(layoutJson);

        _eventStore.Add("warehouse_layout_loaded", null, null, new
        {
            loaded = true
        });
    }

    public object GetWarehouseLayout()
    {
        EnsureInitialized();
        return _gateway.GetWarehouseLayout();
    }

    public async Task<GatewaySnapshotResponse> GetSnapshotAsync(CancellationToken cancellationToken)
    {
        var deviceIds = _gateway.IsInitialized
            ? _gateway.DeviceIds.OrderBy(id => id).ToArray()
            : Array.Empty<string>();

        if (_gateway.IsInitialized)
        {
            await _gateway.GetAllDeviceStatusAsync(cancellationToken);
        }

        return new GatewaySnapshotResponse
        {
            IsInitialized = _gateway.IsInitialized,
            DeviceCount = _gateway.DeviceCount,
            IsQueuePaused = IsQueuePaused,
            EventCount = _eventStore.Count,
            DeviceIds = deviceIds
        };
    }

    public async Task<IReadOnlyList<DeviceStateResponse>> GetDevicesAsync(CancellationToken cancellationToken)
    {
        EnsureInitialized();

        var devices = new List<DeviceStateResponse>();
        foreach (var deviceId in _gateway.DeviceIds.OrderBy(id => id))
        {
            devices.Add(await BuildDeviceStateAsync(deviceId, cancellationToken));
        }

        return devices;
    }

    public async Task<DeviceStateResponse> GetDeviceStatusAsync(string deviceId, CancellationToken cancellationToken)
    {
        EnsureInitialized();
        return await BuildDeviceStateAsync(deviceId, cancellationToken);
    }

    public async Task<Dictionary<string, string>> GetDeviceStatusesAsync(CancellationToken cancellationToken)
    {
        EnsureInitialized();

        var result = new Dictionary<string, string>(StringComparer.OrdinalIgnoreCase);
        foreach (var deviceId in _gateway.DeviceIds.OrderBy(id => id))
        {
            var status = await _gateway.GetDeviceStatusAsync(deviceId, cancellationToken);
            result[deviceId] = status.ToString();
        }

        return result;
    }

    public async Task<Location?> GetActualLocationAsync(string deviceId, CancellationToken cancellationToken)
    {
        EnsureInitialized();
        return await _gateway.GetActualLocationAsync(deviceId, cancellationToken);
    }

    public async Task ActivateDeviceAsync(string deviceId, CancellationToken cancellationToken)
    {
        EnsureInitialized();
        await _gateway.ActivateDevice(deviceId, cancellationToken);
    }

    public async Task<bool> ActivateAllDevicesAsync(CancellationToken cancellationToken)
    {
        EnsureInitialized();
        return await _gateway.ActivateAllDevicesAsync(cancellationToken);
    }

    public async Task DeactivateDeviceAsync(string deviceId)
    {
        EnsureInitialized();
        await _gateway.DeactivateDevice(deviceId);
    }

    public async Task DeactivateAllDevicesAsync()
    {
        EnsureInitialized();
        await _gateway.DeactivateAllDevicesAsync();
    }

    public async Task<bool> ResetDeviceStatusAsync(string deviceId, CancellationToken cancellationToken)
    {
        EnsureInitialized();
        return await _gateway.ResetDeviceStatusAsync(deviceId);
    }

    public void PauseQueue()
    {
        EnsureInitialized();
        _gateway.PauseQueue();
    }

    public void ResumeQueue()
    {
        EnsureInitialized();
        _gateway.ResumeQueue();
    }

    public TransportTask[] GetPendingTasks()
    {
        EnsureInitialized();
        return _gateway.GetPendingTask();
    }

    public TransportTask[] GetProcessingTasks()
    {
        EnsureInitialized();
        return _gateway.GetProccessingTask();
    }

    public async Task<SubmissionResult> SendCommandAsync(TransportTask task)
    {
        EnsureInitialized();
        return await _gateway.SendCommand(task);
    }

    public async Task<SubmissionResult> SendMultipleCommandsAsync(
        IReadOnlyList<TransportTask> tasks,
        CancellationToken cancellationToken)
    {
        EnsureInitialized();
        return await _gateway.SendMultipleCommands(tasks, cancellationToken);
    }

    public bool RemoveCommand(string taskId)
    {
        EnsureInitialized();
        return _gateway.RemoveCommand(taskId);
    }

    public async Task<bool> SendValidationResultAsync(BarcodeValidationRequest request)
    {
        EnsureInitialized();
        return await _gateway.SendValidationResult(
            request.TaskId,
            request.IsValid,
            request.DestinationLocation,
            request.Direction,
            request.GateNumber);
    }

    private async Task<DeviceStateResponse> BuildDeviceStateAsync(string deviceId, CancellationToken cancellationToken)
    {
        var status = await _gateway.GetDeviceStatusAsync(deviceId, cancellationToken);

        return new DeviceStateResponse
        {
            DeviceId = deviceId,
            Connected = _gateway.IsConnected(deviceId),
            Status = status,
            CurrentTasks = _gateway.GetCurrentTasks(deviceId)
        };
    }

    private void SubscribeToEvents()
    {
        _gateway.TaskSucceeded += (_, args) =>
        {
            _eventStore.Add("task_succeeded", args.DeviceId, args.TaskId, new
            {
                args.DeviceId,
                args.TaskId
            });
        };

        _gateway.TaskFailed += (_, args) =>
        {
            _eventStore.Add("task_failed", args.DeviceId, args.TaskId, new
            {
                args.DeviceId,
                args.TaskId,
                error = args.ErrorDetail
            });
        };

        _gateway.TaskAlarm += (_, args) =>
        {
            _eventStore.Add("task_alarm", args.DeviceId, args.TaskId, new
            {
                args.DeviceId,
                args.TaskId,
                error = args.Error
            });
        };

        _gateway.BarcodeReceived += (_, args) =>
        {
            _eventStore.Add("barcode_received", args.DeviceId, args.TaskId, new
            {
                args.DeviceId,
                args.TaskId,
                args.Barcode,
                args.RequestedAt
            });
        };

        _gateway.AlarmHandlingStarted += (_, args) =>
        {
            _eventStore.Add("alarm_handling_started", args.DeviceId, null, new
            {
                args.DeviceId,
                args.TriggerSignal,
                args.Error
            });
        };

        _gateway.AlarmHandlingProgress += (_, args) =>
        {
            _eventStore.Add("alarm_handling_progress", args.DeviceId, null, new
            {
                args.DeviceId,
                args.State,
                args.TriggerSignal,
                args.Error
            });
        };

        _gateway.RuleViolated += (_, args) =>
        {
            _eventStore.Add("rule_violated", null, args.TriggeringCommandId, new
            {
                args.ViolationType,
                args.Description,
                args.Shuttle1Id,
                args.Shuttle1Location,
                args.Shuttle1Status,
                args.Shuttle2Id,
                args.Shuttle2Location,
                args.Shuttle2Status,
                args.Timestamp,
                args.TriggeringCommandId
            });
        };
    }

    private async Task<string> ResolveRequiredJsonAsync(
        string? inlineJson,
        string? explicitPath,
        string? configuredPath,
        string description,
        CancellationToken cancellationToken)
    {
        var json = await ResolveOptionalJsonAsync(
            inlineJson,
            explicitPath,
            configuredPath,
            cancellationToken);

        if (string.IsNullOrWhiteSpace(json))
        {
            throw new ArgumentException(
                $"Missing {description}. Provide inline JSON or a file path in the request/appsettings.");
        }

        return json;
    }

    private async Task<string?> ResolveOptionalJsonAsync(
        string? inlineJson,
        string? explicitPath,
        string? configuredPath,
        CancellationToken cancellationToken)
    {
        if (!string.IsNullOrWhiteSpace(inlineJson))
        {
            return inlineJson;
        }

        var path = explicitPath;
        if (string.IsNullOrWhiteSpace(path))
        {
            path = configuredPath;
        }

        if (string.IsNullOrWhiteSpace(path))
        {
            return null;
        }

        var resolvedPath = ResolveContentPath(path);
        if (!File.Exists(resolvedPath))
        {
            throw new FileNotFoundException($"Configuration file not found: {resolvedPath}", resolvedPath);
        }

        return await File.ReadAllTextAsync(resolvedPath, cancellationToken);
    }

    private string ResolveContentPath(string path)
    {
        return Path.IsPathRooted(path)
            ? path
            : Path.GetFullPath(Path.Combine(_environment.ContentRootPath, path));
    }

    private void EnsureInitialized()
    {
        if (!_gateway.IsInitialized)
        {
            throw new InvalidOperationException(
                "AutomationGateway has not been initialized yet. Call POST /api/gateway/initialize first.");
        }
    }
}
