using System.Text.Json.Serialization;
using Microsoft.AspNetCore.Diagnostics;
using WcsBridgeApi.Auth;
using WcsBridgeApi.Contracts;
using WcsBridgeApi.Services;

var builder = WebApplication.CreateBuilder(args);

builder.Services.ConfigureHttpJsonOptions(options =>
{
    options.SerializerOptions.Converters.Add(new JsonStringEnumConverter());
});

builder.Services.Configure<WcsBridgeOptions>(
    builder.Configuration.GetSection(WcsBridgeOptions.SectionName));

builder.Services.AddSingleton<GatewayEventStore>();
builder.Services.AddSingleton<WcsGatewayService>();

var app = builder.Build();

app.UseExceptionHandler(handler =>
{
    handler.Run(async context =>
    {
        var error = context.Features.Get<IExceptionHandlerFeature>()?.Error;

        var statusCode = error switch
        {
            ArgumentException => StatusCodes.Status400BadRequest,
            FileNotFoundException => StatusCodes.Status400BadRequest,
            InvalidOperationException => StatusCodes.Status409Conflict,
            _ => StatusCodes.Status500InternalServerError
        };

        context.Response.StatusCode = statusCode;
        context.Response.ContentType = "application/json";

        await context.Response.WriteAsJsonAsync(new
        {
            error = error?.GetType().Name ?? "UnknownError",
            message = error?.Message ?? "An unexpected error occurred."
        });
    });
});

app.UseMiddleware<ApiKeyMiddleware>();

app.MapGet("/", (WcsGatewayService gateway, GatewayEventStore events) => Results.Ok(new
{
    service = "wcs-bridge-api",
    description = "HTTP bridge between ERPNext and TQG.Automation.SDK.dll",
    initialized = gateway.IsInitialized,
    deviceCount = gateway.DeviceCount,
    eventCount = events.Count,
    endpoints = new[]
    {
        "/health",
        "/api/gateway/initialize",
        "/api/gateway/devices",
        "/api/gateway/devices/status",
        "/api/gateway/commands",
        "/api/gateway/events"
    }
}));

app.MapGet("/health", (WcsGatewayService gateway, GatewayEventStore events) => Results.Ok(new
{
    status = "ok",
    initialized = gateway.IsInitialized,
    deviceCount = gateway.DeviceCount,
    eventCount = events.Count,
    queuePaused = gateway.IsQueuePaused
}));

var gatewayGroup = app.MapGroup("/api/gateway");

gatewayGroup.MapPost("/initialize", async (
    InitializeGatewayRequest request,
    WcsGatewayService gateway,
    CancellationToken cancellationToken) =>
{
    var snapshot = await gateway.InitializeAsync(request, cancellationToken);
    return Results.Ok(snapshot);
});

gatewayGroup.MapGet("/state", async (WcsGatewayService gateway, CancellationToken cancellationToken) =>
{
    var snapshot = await gateway.GetSnapshotAsync(cancellationToken);
    return Results.Ok(snapshot);
});

gatewayGroup.MapPost("/layout", async (
    LoadWarehouseLayoutRequest request,
    WcsGatewayService gateway,
    CancellationToken cancellationToken) =>
{
    await gateway.LoadWarehouseLayoutAsync(request, cancellationToken);
    var snapshot = await gateway.GetSnapshotAsync(cancellationToken);
    return Results.Ok(snapshot);
});

gatewayGroup.MapGet("/layout", (WcsGatewayService gateway) =>
{
    return Results.Ok(gateway.GetWarehouseLayout());
});

gatewayGroup.MapGet("/devices", async (WcsGatewayService gateway, CancellationToken cancellationToken) =>
{
    var devices = await gateway.GetDevicesAsync(cancellationToken);
    return Results.Ok(devices);
});

gatewayGroup.MapGet("/devices/status", async (WcsGatewayService gateway, CancellationToken cancellationToken) =>
{
    var statuses = await gateway.GetDeviceStatusesAsync(cancellationToken);
    return Results.Ok(statuses);
});

gatewayGroup.MapGet("/devices/{deviceId}/status", async (
    string deviceId,
    WcsGatewayService gateway,
    CancellationToken cancellationToken) =>
{
    var status = await gateway.GetDeviceStatusAsync(deviceId, cancellationToken);
    return Results.Ok(status);
});

gatewayGroup.MapGet("/devices/{deviceId}/location", async (
    string deviceId,
    WcsGatewayService gateway,
    CancellationToken cancellationToken) =>
{
    var location = await gateway.GetActualLocationAsync(deviceId, cancellationToken);
    return Results.Ok(new
    {
        deviceId,
        location
    });
});

gatewayGroup.MapPost("/devices/{deviceId}/activate", async (
    string deviceId,
    WcsGatewayService gateway,
    CancellationToken cancellationToken) =>
{
    await gateway.ActivateDeviceAsync(deviceId, cancellationToken);
    return Results.Ok(new
    {
        deviceId,
        activated = true
    });
});

gatewayGroup.MapPost("/devices/activate-all", async (WcsGatewayService gateway, CancellationToken cancellationToken) =>
{
    var result = await gateway.ActivateAllDevicesAsync(cancellationToken);
    return Results.Ok(new
    {
        activated = result
    });
});

gatewayGroup.MapPost("/devices/{deviceId}/deactivate", async (
    string deviceId,
    WcsGatewayService gateway) =>
{
    await gateway.DeactivateDeviceAsync(deviceId);
    return Results.Ok(new
    {
        deviceId,
        deactivated = true
    });
});

gatewayGroup.MapPost("/devices/deactivate-all", async (WcsGatewayService gateway) =>
{
    await gateway.DeactivateAllDevicesAsync();
    return Results.Ok(new
    {
        deactivated = true
    });
});

gatewayGroup.MapPost("/devices/{deviceId}/reset", async (
    string deviceId,
    WcsGatewayService gateway,
    CancellationToken cancellationToken) =>
{
    var result = await gateway.ResetDeviceStatusAsync(deviceId, cancellationToken);
    return Results.Ok(new
    {
        deviceId,
        reset = result
    });
});

gatewayGroup.MapPost("/queue/pause", (WcsGatewayService gateway) =>
{
    gateway.PauseQueue();
    return Results.Ok(new
    {
        queuePaused = gateway.IsQueuePaused
    });
});

gatewayGroup.MapPost("/queue/resume", (WcsGatewayService gateway) =>
{
    gateway.ResumeQueue();
    return Results.Ok(new
    {
        queuePaused = gateway.IsQueuePaused
    });
});

gatewayGroup.MapGet("/tasks/pending", (WcsGatewayService gateway) => Results.Ok(gateway.GetPendingTasks()));

gatewayGroup.MapGet("/tasks/processing", (WcsGatewayService gateway) => Results.Ok(gateway.GetProcessingTasks()));

gatewayGroup.MapPost("/commands", async (
    SendCommandRequest request,
    WcsGatewayService gateway) =>
{
    var result = await gateway.SendCommandAsync(request.Task);
    return Results.Ok(result);
});

gatewayGroup.MapPost("/commands/batch", async (
    SendBatchCommandsRequest request,
    WcsGatewayService gateway,
    CancellationToken cancellationToken) =>
{
    var result = await gateway.SendMultipleCommandsAsync(request.Tasks, cancellationToken);
    return Results.Ok(result);
});

gatewayGroup.MapDelete("/commands/{taskId}", (string taskId, WcsGatewayService gateway) =>
{
    var removed = gateway.RemoveCommand(taskId);
    return Results.Ok(new
    {
        taskId,
        removed
    });
});

gatewayGroup.MapPost("/barcode-validations", async (
    BarcodeValidationRequest request,
    WcsGatewayService gateway) =>
{
    var accepted = await gateway.SendValidationResultAsync(request);
    return Results.Ok(new
    {
        request.TaskId,
        accepted
    });
});

gatewayGroup.MapGet("/events", (long? afterSequence, int? limit, GatewayEventStore events) =>
{
    var response = events.Read(afterSequence ?? 0, limit ?? 100);
    return Results.Ok(response);
});

var gatewayService = app.Services.GetRequiredService<WcsGatewayService>();
await gatewayService.TryAutoInitializeAsync(app.Lifetime.ApplicationStopping);

app.Run();
