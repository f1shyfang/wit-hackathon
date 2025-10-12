# \ Deployment Guide

## Prerequisites

- Docker
- Docker Compose
- Git (to clone the repository)

## Quick Start

1. **Clone the repository**
   ```bash
   git clone <your-repo-url>
   cd wit-hackathon
   ```

2. **Start the backend**
   ```bash
   docker-compose up -d
   ```

3. **Verify it's running**
   ```bash
   curl http://localhost:52513/api/health
   ```

## Management Commands

### Start services
```bash
docker-compose up -d
```

### View logs
```bash
docker-compose logs -f backend
```

### Stop services
```bash
docker-compose down
```

### Rebuild and restart
```bash
docker-compose down
docker-compose up -d --build
```

## Configuration

### Environment Variables

The backend uses these environment variables (set in docker-compose.yml):

- `NOTREALLY_DB_PATH=/tmp/notreally.db` - SQLite database path
- `NOTREALLY_UPLOAD_DIR=/tmp/uploads` - Temporary upload directory
- `PORT=52513` - Server port

### Audio Features

By default, audio features are **disabled**. To enable:

1. Edit `docker-compose.yml`
2. Add environment variable:
   ```yaml
   environment:
     - NOTREALLY_ENABLE_AUDIO=true
   ```
3. Restart: `docker-compose restart`

## Access

- **Backend API**: http://localhost:52513
- **Health Check**: http://localhost:52513/api/health
- **API Documentation**: http://localhost:52513/

## Frontend Configuration

Update your frontend's environment variable:

```bash
# For local development
NEXT_PUBLIC_API_BASE_URL=http://localhost:52513

# For production (replace with your server IP)
NEXT_PUBLIC_API_BASE_URL=http://your-server-ip:52513
```

## Production Considerations

For production deployment, consider:

1. **Reverse Proxy**: Use nginx or Traefik for HTTPS
2. **Rate Limiting**: Implement request throttling
3. **Monitoring**: Add logging and metrics
4. **Backup**: Regular database backups if using persistent storage
5. **Security**: Firewall rules, container security scanning

## Troubleshooting

### Container won't start
```bash
docker-compose logs backend
```

### Port already in use
```bash
# Check what's using port 52513
lsof -i :52513
# Or change the port in docker-compose.yml
```

### Model file missing
Ensure `backend/model.pkl` exists before building:
```bash
ls -la backend/model.pkl
```

### Health check failing
```bash
# Check if the service is responding
curl -v http://localhost:52513/
```
