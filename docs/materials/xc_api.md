# XC API

`player_api.php?username=a&password=b`

```json
{
  "user_info": {
    "username": "a",
    "password": "b",
    "message": "Server Welcome Message",
    "auth": 1,
    "status": "Active",
    "exp_date": "1750000000",
    "is_trial": "0",
    "active_cons": "0",
    "created_at": "1740000000",
    "max_connections": "1",
    "allowed_output_formats": ["m3u8", "ts", "rtmp"]
  },
  "server_info": {
    "url": "xc.example.com",
    "port": "80",
    "https_port": "443",
    "server_protocol": "http",
    "rtmp_port": "25462",
    "timezone": "Australia/Perth",
    "timestamp_now": 1745000000,
    "time_now": "2025-04-18 18:30:20",
    "process": true
  }
}
```

`player_api.php?action=get_live_categories&username=a&password=b`

```json
[
  {
    "category_id": "22",
    "category_name": "Sports",
    "parent_id": 0
  },
  {
    "category_id": "1",
    "category_name": "Movies",
    "parent_id": 0
  },
  {
    "category_id": "4",
    "category_name": "News",
    "parent_id": 0
  }
]
```

`player_api.php?action=get_live_streams&username=a&password=b`

```json
[
  {
    "num": 1,
    "name": "My Sports Channel",
    "stream_type": "live",
    "stream_id": 4,
    "stream_icon": "",
    "epg_channel_id": "",
    "added": "1500000000",
    "is_adult": 0,
    "category_id": "22",
    "category_ids": [22],
    "custom_sid": null,
    "tv_archive": 0,
    "direct_source": "",
    "tv_archive_duration": 0
  },
  {
    "num": 2,
    "name": "My News Channel",
    "stream_type": "live",
    "stream_id": 7,
    "stream_icon": "",
    "epg_channel_id": "",
    "added": "1500000000",
    "is_adult": 0,
    "category_id": "4",
    "category_ids": [4],
    "custom_sid": null,
    "tv_archive": 0,
    "direct_source": "",
    "tv_archive_duration": 0
  }
]
```
