using TQG.Automation.SDK.Shared;

namespace WcsBridgeApi.Contracts;

public sealed record InitializeGatewayRequest
{
    public string? ConfigurationJson { get; init; }

    public string? ConfigurationPath { get; init; }

    public string? WarehouseLayoutJson { get; init; }

    public string? WarehouseLayoutPath { get; init; }

    public bool ActivateAllDevices { get; init; }
}

public sealed record LoadWarehouseLayoutRequest
{
    public string? LayoutJson { get; init; }

    public string? LayoutPath { get; init; }
}

public sealed record SendCommandRequest
{
    public required TransportTask Task { get; init; }
}

public sealed record SendBatchCommandsRequest
{
    public required IReadOnlyList<TransportTask> Tasks { get; init; }
}

public sealed record BarcodeValidationRequest
{
    public required string TaskId { get; init; }

    public required bool IsValid { get; init; }

    public Location? DestinationLocation { get; init; }

    public Direction? Direction { get; init; }

    public int? GateNumber { get; init; }
}
