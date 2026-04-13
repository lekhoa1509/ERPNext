namespace WcsBridgeApi.Services;

public sealed class WcsBridgeOptions
{
    public const string SectionName = "WcsBridge";

    public string ApiKey { get; set; } = "change-this-api-key";

    public int EventBufferSize { get; set; } = 500;

    public string? GatewayConfigurationPath { get; set; }

    public string? WarehouseLayoutPath { get; set; }

    public bool ActivateAllDevicesOnStartup { get; set; }
}
