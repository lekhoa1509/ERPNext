using TQG.Automation.SDK.Shared;

namespace WcsBridgeApi.Contracts;

public sealed record GatewaySnapshotResponse
{
    public required bool IsInitialized { get; init; }

    public required int DeviceCount { get; init; }

    public required bool IsQueuePaused { get; init; }

    public required int EventCount { get; init; }

    public required IReadOnlyList<string> DeviceIds { get; init; }
}

public sealed record DeviceStateResponse
{
    public required string DeviceId { get; init; }

    public required bool Connected { get; init; }

    public required DeviceStatus Status { get; init; }

    public required string[] CurrentTasks { get; init; }
}

public sealed record GatewayEventRecord(
    long Sequence,
    string Type,
    DateTimeOffset OccurredAt,
    string? DeviceId,
    string? TaskId,
    object Payload);

public sealed record GatewayEventsResponse(
    long LatestSequence,
    int Count,
    IReadOnlyList<GatewayEventRecord> Events);
