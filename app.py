import asyncio
import logging
from aiohttp import web


from bot import bot, dp, router  
async def polling_task():
    await bot.delete_webhook(drop_pending_updates=True)
    dp.include_router(router)
    await dp.start_polling(bot, allowed_updates=["message", "callback_query"])

async def on_startup(app: web.Application):
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    app["poller"] = asyncio.create_task(polling_task())
    logging.info("Polling started")

async def on_shutdown(app: web.Application):
    poller = app.get("poller")
    if poller:
        poller.cancel()
        try:
            await poller
        except asyncio.CancelledError:
            pass
    await bot.session.close()

async def health(_request: web.Request) -> web.Response:
    return web.Response(text="ok")

def create_app() -> web.Application:
    app = web.Application()
    app.router.add_get("/", health)
    app.router.add_get("/healthz", health)
    app.on_startup.append(on_startup)
    app.on_shutdown.append(on_shutdown)
    return app

app = create_app()

if __name__ == "__main__":
    web.run_app(app, host="0.0.0.0", port=8080)
