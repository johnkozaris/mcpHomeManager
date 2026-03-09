## Custom Tools

Add custom tools to any service via the web UI:

```json:tool-definition.json
{
  "name": "get_temperature",
  "description": "Get current temperature from sensor",
  "method": "GET",
  "path": "/api/sensors/temperature",
  "parameters": {
    "sensor_id": {
      "type": "string",
      "description": "The sensor ID",
      "required": true
    }
  }
}
```
