# WCS Bridge API

Service ASP.NET Core nho de ERPNext goi HTTP vao `TQG.Automation.SDK.dll` thay vi nhung DLL truc tiep.

## Muc tieu

- Dung `TQG.Automation.SDK.dll` da build san.
- Xuat HTTP API cho ERPNext/Frappe goi.
- Luu event trong memory de ERPNext poll ket qua task, alarm, barcode validation.
- Bao ve bang `X-API-Key`.

## Vi tri DLL tham chieu

Bridge nay tham chieu file:

- [TQG.Automation.SDK.dll](/Users/lekhoa.lekhoa2gmail.com/Downloads/ERPNext/services/wcs-bridge-api/lib/TQG.Automation.SDK.dll)

Neu ban build DLL moi, chi can copy de len file tren roi build lai bridge.

## Chay local

```bash
cd /Users/lekhoa.lekhoa2gmail.com/Downloads/ERPNext/services/wcs-bridge-api
dotnet run --urls http://127.0.0.1:5057
```

Mac dinh service doc `appsettings.json`.

## Cau hinh

`appsettings.json`

```json
{
  "WcsBridge": {
    "ApiKey": "change-this-api-key",
    "EventBufferSize": 500,
    "GatewayConfigurationPath": "",
    "WarehouseLayoutPath": "",
    "ActivateAllDevicesOnStartup": false
  }
}
```

Ban co 2 cach initialize:

1. Set `GatewayConfigurationPath` + `WarehouseLayoutPath` trong `appsettings.json` de service auto-init khi start.
2. Goi `POST /api/gateway/initialize` va gui JSON/path tu ERPNext.

## Endpoint chinh

- `GET /health`
- `POST /api/gateway/initialize`
- `GET /api/gateway/state`
- `GET /api/gateway/devices`
- `GET /api/gateway/devices/status`
- `POST /api/gateway/devices/activate-all`
- `POST /api/gateway/commands`
- `POST /api/gateway/commands/batch`
- `DELETE /api/gateway/commands/{taskId}`
- `POST /api/gateway/barcode-validations`
- `GET /api/gateway/events?afterSequence=0&limit=100`

Moi endpoint tru `/` va `/health` deu can header:

```http
X-API-Key: change-this-api-key
```

## Vi du initialize bang file path

```bash
curl -X POST http://127.0.0.1:5057/api/gateway/initialize \
  -H 'Content-Type: application/json' \
  -H 'X-API-Key: change-this-api-key' \
  -d '{
    "configurationPath": "/absolute/path/to/plc-gateway.json",
    "warehouseLayoutPath": "/absolute/path/to/warehouse-layout.json",
    "activateAllDevices": true
  }'
```

## Vi du gui command

```bash
curl -X POST http://127.0.0.1:5057/api/gateway/commands \
  -H 'Content-Type: application/json' \
  -H 'X-API-Key: change-this-api-key' \
  -d '{
    "task": {
      "taskId": "SO-0001",
      "deviceId": "Shuttle01",
      "commandType": "Outbound",
      "sourceLocation": {
        "floor": 1,
        "rail": 13,
        "block": 5,
        "depth": 1
      },
      "gateNumber": 1,
      "inDirBlock": "Bottom",
      "outDirBlock": "Bottom"
    }
  }'
```

## Vi du ERPNext Python

```python
import requests

base_url = "http://127.0.0.1:5057"
headers = {
    "X-API-Key": "change-this-api-key",
    "Content-Type": "application/json",
}

payload = {
    "task": {
        "taskId": "SO-0001",
        "deviceId": "Shuttle01",
        "commandType": "Outbound",
        "sourceLocation": {"floor": 1, "rail": 13, "block": 5, "depth": 1},
        "gateNumber": 1,
        "inDirBlock": "Bottom",
        "outDirBlock": "Bottom",
    }
}

response = requests.post(f"{base_url}/api/gateway/commands", json=payload, headers=headers, timeout=30)
response.raise_for_status()
print(response.json())
```

## Luong goi de nghi cho ERPNext

1. ERPNext goi `POST /api/gateway/initialize` khi bridge chua init.
2. ERPNext goi `POST /api/gateway/commands` de day lenh.
3. ERPNext poll `GET /api/gateway/events` de nhan `task_succeeded`, `task_failed`, `task_alarm`, `barcode_received`.
4. Khi co `barcode_received`, ERPNext validate business rule roi goi `POST /api/gateway/barcode-validations`.
