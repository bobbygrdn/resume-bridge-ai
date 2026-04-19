import uvicorn
import os
import asyncio

if __name__ == "__main__":
    if os.name == 'nt':
        asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
    
    # Set reload=False to bypass the Windows subprocess bug
    uvicorn.run("src.main:app", host="127.0.0.1", port=8000, reload=False)