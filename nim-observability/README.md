# NIM Observability Stack

A complete Docker Compose-based observability stack for monitoring your NIM LLM metrics with Prometheus and Grafana.

## Quick Start

1. **Start the stack:**
   ```bash
   cd nim-observability
   docker compose up -d
   ```

2. **Verify Prometheus target:**
   - Open [http://localhost:9090/targets](http://localhost:9090/targets)
   - Look for "nim-llm" target showing **UP**

3. **Access Grafana:**
   - Open [http://localhost:3000](http://localhost:3000)
   - Login: `admin/admin` (default credentials)
   - Navigate to the **NIM** folder to see your dashboard

## Configuration

### Environment Variables (.env)

The `.env` file contains all configuration. Key settings:

- `LLM_HOST=192.168.5.173` - Your LLM server IP
- `LLM_PORT=8000` - Your LLM server port
- `LLM_METRICS_PATH=/v1/metrics` - Metrics endpoint path
- `PROM_SCRAPE_INTERVAL=5s` - How often Prometheus scrapes metrics
- `PROM_RETENTION=15d` - How long to keep metrics data

### LLM Host Configuration

If your LLM runs on the same host (outside Docker), the current configuration should work. If you need to change the LLM host:

1. Edit `.env` file:
   ```env
   LLM_HOST=your-llm-ip
   LLM_PORT=8000
   ```

2. Restart the stack:
   ```bash
   docker compose down
   docker compose up -d
   ```

## Dashboard Features

The NIM dashboard includes:

- **Time to First Token (TTFT)** - p50, p90, p99 percentiles
- **Inter-Token Latency (ITL)** - p50, p90, p99 percentiles
- **Token Generation Throughput** - tokens per second
- **Requests Per Second (RPS)** - request rate
- **Request Queue Status** - waiting vs running requests
- **KV Cache Utilization** - GPU cache usage percentage
- **Prompt Tokens Distribution** - p50, p90, p99 percentiles
- **Generated Tokens Distribution** - p50, p90, p99 percentiles

## Alerting

Sample alerts are configured in `prometheus/rules/nim-alerts.yml`:

- **High KV Cache Usage** - >90% cache utilization
- **Requests Backing Up** - >2 requests waiting for 3+ minutes
- **Slow TTFT p90** - >1.5s time to first token
- **High Error Rate** - >5% error rate
- **Low Throughput** - <10 tokens/sec

View alerts at [http://localhost:9090/alerts](http://localhost:9090/alerts)

## Troubleshooting

### Prometheus can't reach LLM

1. **Test connectivity from host:**
   ```bash
   curl http://192.168.5.173:8000/v1/metrics | head
   ```

2. **Test from Prometheus container:**
   ```bash
   docker exec -it prometheus sh -c 'curl -s http://192.168.5.173:8000/v1/metrics | head'
   ```

3. **Check Prometheus targets:**
   - Go to [http://localhost:9090/targets](http://localhost:9090/targets)
   - Look for error messages

### Grafana shows no data

1. **Check datasource:**
   - Go to Grafana → Configuration → Data Sources
   - Verify Prometheus datasource is working

2. **Check dashboard queries:**
   - Open dashboard → Panel → Edit
   - Verify queries match your metrics

### Common Issues

- **Linux host access**: The `extra_hosts` configuration maps `host.docker.internal` to the Docker host gateway
- **Firewall**: Ensure ports 9090 (Prometheus) and 3000 (Grafana) are accessible
- **Metrics format**: Ensure your LLM exposes metrics in Prometheus format at `/v1/metrics`

## Management Commands

```bash
# Start stack
docker compose up -d

# Stop stack
docker compose down

# Stop and delete all data (careful!)
docker compose down -v

# View logs
docker compose logs -f

# Restart services
docker compose restart
```

## Security Notes

- Change default Grafana credentials in `.env` before production use
- Consider adding authentication/authorization for production deployments
- The current setup is designed for development/testing environments

## File Structure

```
nim-observability/
├── .env                           # Environment configuration
├── docker-compose.yml            # Docker Compose services
├── prometheus/
│   ├── prometheus.yml            # Prometheus configuration
│   └── rules/
│       └── nim-alerts.yml        # Alert rules
└── grafana/
    └── provisioning/
        ├── datasources/
        │   └── datasource.yml    # Prometheus datasource
        └── dashboards/
            ├── dashboards.yml    # Dashboard provisioning
            └── nim-dashboard.json # NIM dashboard definition
```
