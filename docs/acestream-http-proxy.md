# AceStream HTTP Proxy

```bash
docker run -d -t -p 127.0.0.1:6878:6878 ghcr.io/martinbjeldbak/acestream-http-proxy
```

Or if you are in a network without UPnP, you will need to port forward 8621

```bash
docker run -d -t -p 127.0.0.1:6878:6878 -p 8621:8621 ghcr.io/martinbjeldbak/acestream-http-proxy
```
