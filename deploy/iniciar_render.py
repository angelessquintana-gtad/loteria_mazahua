"""Arranque de una sola instancia en Render Free (sin shell ni predeploy de pago)."""
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
os.environ['AUTO_MIGRATE'] = 'true'
os.environ['SERIAL_ENABLED'] = 'false'
os.environ.setdefault('DB_POOL_TIMEOUT', '60')
import main

if __name__ == '__main__':
    import uvicorn
    uvicorn.run(main.app, host='0.0.0.0', port=int(os.getenv('PORT', '10000')), workers=1,
                proxy_headers=True, forwarded_allow_ips='*', limit_concurrency=128,
                ws_max_size=4096, access_log=False)
