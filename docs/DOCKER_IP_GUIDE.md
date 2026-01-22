# Docker IP Address Guide for Monitoring

## ⚠️ Important: Container IPs Change!

If you're using the Docker container IP (like `172.18.0.2`), **it WILL change** and break your monitoring.

## When Container IPs Change

Container IPs change when:
- ✗ Container restarts (`docker-compose restart`)
- ✗ Docker daemon restarts
- ✗ Running `docker-compose down` then `up`
- ✗ Recreating the container
- ✗ Network gets recreated

## ✅ Recommended Solutions

### Option 1: Use Docker Host IP (BEST)

**Why:** Port 5000 is already mapped from container to host, so use the stable host IP.

```bash
# Get your Docker host IP
hostname -I | awk '{print $1}'
# Example output: 192.168.1.100

# Test it works
curl http://192.168.1.100:5000/metrics

# Use in Prometheus
targets: ['192.168.1.100:5000']
```

**Pros:**
- ✅ IP never changes
- ✅ Works even after container restarts
- ✅ Simple to configure
- ✅ No docker-compose changes needed

**Cons:**
- Need to know your host IP (easy: `hostname -I`)

### Option 2: Use Docker Service Name with DNS

If Prometheus runs in Docker on the same network:

```yaml
# In your docker-compose.yml
services:
  web:
    container_name: iam-job-scout-web-1
    networks:
      - monitoring

  prometheus:
    image: prom/prometheus
    networks:
      - monitoring
    volumes:
      - ./prometheus.yml:/etc/prometheus/prometheus.yml

networks:
  monitoring:
    driver: bridge
```

```yaml
# In prometheus.yml
scrape_configs:
  - job_name: 'iam-job-scout'
    static_configs:
      - targets: ['iam-job-scout-web-1:5000']  # Use container name
```

**Pros:**
- ✅ Automatic DNS resolution
- ✅ Works even after restarts
- ✅ Clean configuration

**Cons:**
- Requires Prometheus in Docker
- Both services must be on same network

### Option 3: Static Container IP (Advanced)

Create a custom network with fixed IP:

```yaml
# docker-compose.yml
version: '3.8'

services:
  web:
    build: .
    networks:
      monitoring:
        ipv4_address: 172.20.0.10  # Fixed IP
    ports:
      - "5000:5000"

networks:
  monitoring:
    driver: bridge
    ipam:
      config:
        - subnet: 172.20.0.0/16
          gateway: 172.20.0.1
```

```yaml
# prometheus.yml
targets: ['172.20.0.10:5000']
```

**Pros:**
- ✅ IP is predictable and fixed
- ✅ Works after restarts

**Cons:**
- More complex configuration
- Need to manage subnet ranges
- Can conflict with other networks

### Option 4: Host Network Mode (Simple but Less Isolated)

```yaml
# docker-compose.yml
services:
  web:
    build: .
    network_mode: "host"
    # Remove ports: section (not needed)
```

```yaml
# prometheus.yml
targets: ['localhost:5000']  # or '127.0.0.1:5000'
```

**Pros:**
- ✅ Very simple
- ✅ Uses localhost
- ✅ No port mapping needed

**Cons:**
- ✗ Less network isolation
- ✗ Can't run multiple instances on same port
- ✗ Not recommended for production

## 🎯 Our Recommendation

**Use Docker Host IP** (Option 1) - It's the best balance of:
- ✅ Simplicity
- ✅ Stability  
- ✅ No docker-compose changes
- ✅ Works with external Prometheus

## Quick Reference

| Method | Stability | Complexity | Recommended |
|--------|-----------|------------|-------------|
| Host IP | ⭐⭐⭐⭐⭐ | ⭐ Simple | ✅ Yes |
| Container IP | ⭐ Changes | ⭐ Simple | ❌ No |
| Docker DNS | ⭐⭐⭐⭐⭐ | ⭐⭐ Medium | ✅ Yes (if Prometheus in Docker) |
| Static IP | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ Complex | ⚠️ Maybe |
| Host Network | ⭐⭐⭐⭐⭐ | ⭐ Simple | ⚠️ Testing only |

## Testing Your Setup

```bash
# 1. Get your chosen IP
hostname -I | awk '{print $1}'

# 2. Test metrics endpoint
curl http://YOUR_IP:5000/metrics

# 3. Test health endpoint
curl http://YOUR_IP:5000/health

# 4. Restart container and test again
docker-compose restart web
sleep 5
curl http://YOUR_IP:5000/metrics  # Should still work!
```

## Troubleshooting

### Prometheus Target Goes DOWN After Restart

**You used container IP instead of host IP.**

```bash
# Fix it:
# 1. Get host IP
hostname -I | awk '{print $1}'

# 2. Update prometheus.yml
sudo nano /etc/prometheus/prometheus.yml
# Change container IP to host IP

# 3. Reload
curl -X POST http://192.168.60.2:9090/-/reload
```

### Can't Reach Metrics from Prometheus Server

```bash
# From Prometheus server, test connectivity
ping YOUR_HOST_IP
curl http://YOUR_HOST_IP:5000/metrics

# Check firewall
sudo ufw status
sudo ufw allow 5000/tcp
```

---

**Remember:** Use your Docker **host IP**, not the container IP!
