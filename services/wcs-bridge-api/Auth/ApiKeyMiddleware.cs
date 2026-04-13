using Microsoft.Extensions.Options;
using WcsBridgeApi.Services;

namespace WcsBridgeApi.Auth;

public sealed class ApiKeyMiddleware
{
    private readonly RequestDelegate _next;
    private readonly IOptions<WcsBridgeOptions> _options;

    public ApiKeyMiddleware(RequestDelegate next, IOptions<WcsBridgeOptions> options)
    {
        _next = next;
        _options = options;
    }

    public async Task InvokeAsync(HttpContext context)
    {
        if (IsPublicPath(context.Request.Path))
        {
            await _next(context);
            return;
        }

        var expectedApiKey = _options.Value.ApiKey?.Trim();
        if (string.IsNullOrEmpty(expectedApiKey))
        {
            await _next(context);
            return;
        }

        if (!context.Request.Headers.TryGetValue("X-API-Key", out var providedApiKey) ||
            !string.Equals(providedApiKey.ToString(), expectedApiKey, StringComparison.Ordinal))
        {
            context.Response.StatusCode = StatusCodes.Status401Unauthorized;
            await context.Response.WriteAsJsonAsync(new
            {
                error = "Unauthorized",
                message = "Missing or invalid X-API-Key header."
            });
            return;
        }

        await _next(context);
    }

    private static bool IsPublicPath(PathString path)
    {
        return path == "/" || path.StartsWithSegments("/health");
    }
}
