$uuid = [guid]::NewGuid().ToString()
$headers = @{
    'x-api-key' = 'sdgdskldFPLGfjHn1421dgnlxdGTbngdflg6290bRjslfihsjhSDsdgGHH25hjf'
    'x-user-key' = 'eyJjaSI6IjYwY2FiYjBiLTU1OTctNDQ4NS04ZjYzLTdlOWUwNTZlMGJiOCIsImVhbiI6IlVucmVnaXN0ZXJlZEFwcGxpY2F0aW9uIiwiZWsiOiJnYU9JNlZjZklFemNSdDcyNDA4QzRFcC56UTVqRXVFcGVEUWRHa3FKTXRqV2pvSjhpQzFnLmdPWU9QOGlGUGZweFQ2Wjk4MzFKVXUtaVhVOFZ2YlUtRHVBWHo3czV4bG5sUTFKbXMwYmIzNF8ifQ__'
    'x-request-id' = $uuid
}
$body = @{
    'InstrumentId' = 1365
    'UnitsToDeduct' = $null
} | ConvertTo-Json
$response = Invoke-WebRequest -Uri 'https://public-api.etoro.com/api/v1/trading/execution/market-close-orders/positions/3377763871' -Headers $headers -Method Post -Body $body -ContentType 'application/json'
$response.Content