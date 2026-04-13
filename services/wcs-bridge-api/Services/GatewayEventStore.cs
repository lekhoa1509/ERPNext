using System.Collections.Concurrent;
using Microsoft.Extensions.Options;
using WcsBridgeApi.Contracts;

namespace WcsBridgeApi.Services;

public sealed class GatewayEventStore
{
    private readonly ConcurrentQueue<GatewayEventRecord> _events = new();
    private readonly int _maxSize;
    private long _lastSequence;
    private int _count;

    public GatewayEventStore(IOptions<WcsBridgeOptions> options)
    {
        _maxSize = Math.Max(10, options.Value.EventBufferSize);
    }

    public int Count => Math.Max(0, _count);

    public GatewayEventRecord Add(string type, string? deviceId, string? taskId, object payload)
    {
        var record = new GatewayEventRecord(
            Interlocked.Increment(ref _lastSequence),
            type,
            DateTimeOffset.UtcNow,
            deviceId,
            taskId,
            payload);

        _events.Enqueue(record);
        Interlocked.Increment(ref _count);
        TrimIfNeeded();
        return record;
    }

    public GatewayEventsResponse Read(long afterSequence, int limit)
    {
        var normalizedLimit = Math.Clamp(limit, 1, _maxSize);

        var records = _events
            .Where(item => item.Sequence > afterSequence)
            .OrderBy(item => item.Sequence)
            .Take(normalizedLimit)
            .ToArray();

        return new GatewayEventsResponse(
            LatestSequence: Interlocked.Read(ref _lastSequence),
            Count: records.Length,
            Events: records);
    }

    private void TrimIfNeeded()
    {
        while (Volatile.Read(ref _count) > _maxSize && _events.TryDequeue(out _))
        {
            Interlocked.Decrement(ref _count);
        }
    }
}
