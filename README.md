dev to main on 05/may/2025

Get-ChildItem -Recurse | Where-Object {
>>     $_.FullName -notlike "*\.venv\*" -and
>>     $_.FullName -notlike "*\__pycache__\*" -and
>>     $_.FullName -notlike "*\secrets\*"
>> } | ForEach-Object { $_.FullName } | Out-File tree.txt