import asyncio
import os
import sys
import time
from telethon import TelegramClient, events, Button
from loguru import logger

from config import settings
from utils.http_client import AsyncHTTPClient
from providers.factory import ProviderFactory, get_provider
from core.processor import VideoProcessor
from core.queue_worker import QueueWorker
from core.uploader import TelegramUploader

# Initialize Client
client = TelegramClient('drama_bot_session', settings.telegram_api_id, settings.telegram_api_hash)
worker = QueueWorker(max_concurrent=settings.max_concurrent_tasks)
processor = VideoProcessor(ffmpeg_path=settings.ffmpeg_path, aria2c_path=settings.aria2c_path)
uploader = TelegramUploader(client)

# Import implementations
import providers.impl.vigloo
import providers.impl.bilitv
import providers.impl.fundrama
import providers.impl.shortmax
import providers.impl.idrama
import providers.impl.dramabite
import providers.impl.dramabox
import providers.impl.stardust
import providers.impl.radreels
import providers.impl.velolo
import providers.impl.hishort
import providers.impl.microdrama
import providers.impl.meloshort
import providers.impl.snackshort
import providers.impl.freereels
import providers.impl.flickreels
import providers.impl.dotdrama
import providers.impl.dramaboxv2
import providers.impl.goodshort

from core.database import db

user_states = {}

async def cleanup_last_msg(chat_id):
    state = user_states.get(chat_id, {})
    last_id = state.get("last_bot_msg")
    if last_id:
        try: await client.delete_messages(chat_id, last_id)
        except: pass

async def track_user(event):
    user = await event.get_sender()
    await db.add_user(user.id, user.username)
    if user.id in settings.admin_list:
        await db.set_admin(user.id, True)
    
    # Auto-cleanup previous user input if requested (optional)
    # user_states.setdefault(user.id, {})


async def notify_admins(text):
    for admin_id in settings.admin_list:
        try:
            await client.send_message(admin_id, text)
        except: pass


async def build_platform_buttons(user_id: int, page: int = 0):
    names = sorted(ProviderFactory.get_provider_names())
    per_page = 8 # 4 rows of 2
    total_pages = (len(names) + per_page - 1) // per_page
    
    start_idx = page * per_page
    end_idx = start_idx + per_page
    current_page_names = names[start_idx:end_idx]
    
    buttons = []
    for i in range(0, len(current_page_names), 2):
        row = [Button.inline(current_page_names[i].upper(), data=f"p:{current_page_names[i]}")]
        if i + 1 < len(current_page_names):
            row.append(Button.inline(current_page_names[i+1].upper(), data=f"p:{current_page_names[i+1]}"))
        buttons.append(row)
    
    # Navigation buttons
    nav_row = []
    if page > 0:
        nav_row.append(Button.inline("⬅️ Previous", data=f"start_page:{page-1}"))
    if page < total_pages - 1:
        nav_row.append(Button.inline("Next ➡️", data=f"start_page:{page+1}"))
    
    if nav_row:
        buttons.append(nav_row)
    
    # Show Admin Panel button ONLY if user is an admin
    if user_id in settings.admin_list:
        buttons.append([Button.inline("🛠️ Admin Panel", data="adm:dashboard")])
        
    return buttons, page + 1, total_pages

async def build_admin_panel():
    total_users = await db.get_total_users()
    active_tasks = worker.pending_count
    text = (f"🛠️ **ADMIN PANEL**\n\n"
            f"👤 Total Users: `{total_users}`\n"
            f"⏳ Active Tasks: `{active_tasks}`\n\n"
            "Select a management option:")
    
    buttons = [
        [Button.inline("➕ Add FSub", data="adm:fsub_add"), Button.inline("➖ Del FSub", data="adm:fsub_del")],
        [Button.inline("📊 View FSub", data="adm:fsub_view"), Button.inline("📢 Broadcast", data="adm:broadcast")],
        [Button.inline("🔑 Add Member", data="adm:add_user"), Button.inline("👥 User List", data="adm:users")],
        [Button.inline("⚙️ System Settings", data="adm:settings"), Button.inline("« Home", data="back_start")]
    ]
    return text, buttons

async def build_settings_panel():
    text = ("⚙️ **SYSTEM SETTINGS**\n\n"
            "Manage bot updates and process lifecycle.")
    buttons = [
        [Button.inline("🔄 /update", data="adm:update"), Button.inline("♻️ /restart", data="adm:restart")],
        [Button.inline("« Back to Admin", data="adm:dashboard")]
    ]
    return text, buttons

@client.on(events.NewMessage(pattern='/id'))
async def id_handler(event):
    await event.respond(f"👤 **User Information**\n\nYour Telegram ID: `{event.sender_id}`\nAccess Status: `{'Authorized' if await db.is_authorized(event.sender_id) else 'Guest'}`")

@client.on(events.NewMessage(pattern='/update'))
async def update_bot_handler(event):
    if event.sender_id not in settings.admin_list:
        return
    
    msg = await event.respond("📡 **Performing Total Update...**")
    try:
        import subprocess
        # Deep Clean Sync
        commands = [
            ['git', 'fetch', '--all'],
            ['git', 'reset', '--hard', 'origin/main'],
            ['git', 'clean', '-fd']
        ]
        
        output = ""
        for cmd in commands:
            proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            stdout, stderr = proc.communicate()
            output += f"**{cmd[1]}**: {stdout[:100]}\n"
        
        await msg.edit(f"✅ **Total Update Complete!**\n\n{output}\n🔄 **Restarting bot...**")
        import sys
        import os
        os.execl(sys.executable, sys.executable, *sys.argv)
    except Exception as e:
        await msg.edit(f"❌ **Total Update failed:** `{e}`")


@client.on(events.NewMessage(pattern='/restart'))
async def restart_bot_handler(event):
    if event.sender_id not in settings.admin_list:
        return await event.respond("❌ Access Denied.")
    
    await event.respond("🔄 **Restarting bot...**")
    import sys
    import os
    os.execl(sys.executable, sys.executable, *sys.argv)

@client.on(events.NewMessage(pattern='/start'))
async def start_handler(event):
    await track_user(event)
    user = await event.get_sender()
    chat_id = event.sender_id
    
    if not await db.is_authorized(chat_id):
        text = (f"❌ **Akses Terbatas**\n\n"
                f"Maaf, bot ini hanya dapat digunakan oleh member terdaftar.\n"
                f"Silahkan hubungi admin untuk aktivasi akses.\n\n"
                f"🆔 **ID Anda**: `{chat_id}`\n"
                f"👤 **Username**: @{user.username if user.username else 'None'}")
        
        buttons = [Button.url("📱 Hubungi Admin", "https://t.me/LokLok_Cs")]
        return await event.respond(text, buttons=buttons)
    
    await cleanup_last_msg(chat_id)
    buttons, cur, total = await build_platform_buttons(event.sender_id)
    msg = await event.respond(
        f"🎬 **Drama Automation Bot**\nSelect your platform below to start browsing:\n\nPage: `{cur}/{total}`",
        buttons=buttons
    )
    user_states.setdefault(event.chat_id, {})["last_bot_msg"] = msg.id

@client.on(events.CallbackQuery(data=lambda d: d.startswith(b"start_page:")))
async def page_callback(event):
    await track_user(event)
    page = int(event.data.decode().split(":")[1])
    buttons, cur, total = await build_platform_buttons(event.sender_id, page)
    await event.edit(
        f"🎬 **Drama Automation Bot**\nSelect your platform below to start browsing:\n\nPage: `{cur}/{total}`",
        buttons=buttons
    )

@client.on(events.NewMessage(pattern='/admin'))
async def admin_handler(event):
    await track_user(event)
    if event.sender_id not in settings.admin_list:
        return await event.respond("❌ Access Denied.")
    
    await cleanup_last_msg(event.chat_id)
    text, buttons = await build_admin_panel()
    msg = await event.respond(text, buttons=buttons)
    user_states.setdefault(event.chat_id, {})["last_bot_msg"] = msg.id

@client.on(events.CallbackQuery(data=lambda d: d.startswith(b"adm:")))
async def admin_callback(event):
    if event.sender_id not in settings.admin_list:
        return await event.answer("❌ Access Denied.", alert=True)
    
    data = event.data.decode().split(":")[1]
    
    try:
        if data == "dashboard":
            text, buttons = await build_admin_panel()
            await event.edit(text, buttons=buttons)
        
        elif data == "users":
            total = await db.get_total_users()
            await event.edit(f"👥 **Total Members**: `{total}`", 
                            buttons=[Button.inline("« Back", data="adm:dashboard")])
        
        elif data == "broadcast":
            user_states[event.chat_id] = {"action": "broadcast_wait"}
            await event.edit("📢 **BROADCAST MODE**\nSend the message you want to broadcast to all users.", 
                            buttons=[Button.inline("« Cancel", data="adm:dashboard")])
    
        elif data == "add_user":
            user_states[event.chat_id] = {"action": "add_user_id"}
            await event.edit("🔑 **ADD MEMBER**\nSilahkan masukan **Telegram ID** user yang ingin diberikan akses:", 
                            buttons=[Button.inline("« Cancel", data="adm:dashboard")])
    
        elif data == "fsub_view":
            channels = await db.get_fsub_channels()
            if not channels:
                text = "📊 **FSub Channels**: None configured."
            else:
                text = "📊 **FSub Channels**:\n" + "\n".join([f"- {c['name']} (`{c['id']}`)" for c in channels])
            await event.edit(text, buttons=[Button.inline("« Back", data="adm:dashboard")])
        
        elif data == "settings":
            text, buttons = await build_settings_panel()
            await event.edit(text, buttons=buttons)
    
        elif data == "update":
            await event.answer("📡 Performing Total Update...")
            import subprocess
            # Clean sync: fetch, reset hard, and clean untracked
            commands = [
                ['git', 'fetch', '--all'],
                ['git', 'reset', '--hard', 'origin/main'],
                ['git', 'clean', '-fd']
            ]
            
            output = ""
            for cmd in commands:
                proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
                stdout, stderr = proc.communicate()
                output += f"**{cmd[1]}**: {stdout[:100]}\n"
    
            await event.respond(f"✅ **Total Update Complete!**\n\n{output}\n🔄 **Restarting bot...**")
            import sys
            import os
            os.execl(sys.executable, sys.executable, *sys.argv)
    
        elif data == "restart":
            await event.respond("🔄 **Restarting bot...**")
            import sys
            import os
            os.execl(sys.executable, sys.executable, *sys.argv)

    
    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        logger.exception("Admin Callback Error")
        admin_report = (f"🚨 **ADMIN PANEL ERROR**\n\n"
                       f"👤 **User**: `{event.chat_id}`\n"
                       f"⚙️ **Action**: `{data}`\n"
                       f"⚠️ **Error**: `{str(e)}`\n\n"
                       f"📋 **Traceback**:\n```{error_details[:3000]}```")
        await notify_admins(admin_report)
        await event.answer(f"❌ Admin Error: {e}", alert=True)



@client.on(events.CallbackQuery(data=lambda d: d.startswith(b"p:")))
async def platform_callback(event):
    await track_user(event)
    platform = event.data.decode().split(":")[1]
    user_states[event.chat_id] = {"platform": platform, "action": "idle"}
    
    if platform == "freereels":
        buttons = [
            [Button.inline("🔍 Search", data=f"act:search:query:{platform}")],
            [
                Button.inline("🔥 For You", data=f"act:disc:foryou:{platform}"),
                Button.inline("📈 Popular", data=f"act:disc:popular:{platform}")
            ],
            [
                Button.inline("✨ New", data=f"act:disc:latest:{platform}"),
                Button.inline("🎙️ Dubbing", data=f"act:disc:dubbed:{platform}")
            ],
            [
                Button.inline("👩 Female", data=f"act:disc:female:{platform}"),
                Button.inline("👨 Male", data=f"act:disc:male:{platform}")
            ],
            [
                Button.inline("🎎 Anime", data=f"act:disc:anime:{platform}"),
                Button.inline("⏳ Soon", data=f"act:disc:coming-soon:{platform}")
            ],
            [Button.inline("⬅️ Back", data="back_start")]
        ]
    elif platform == "flickreels":
        buttons = [
            [Button.inline("🔍 Search", data=f"act:search:query:{platform}")],
            [
                Button.inline("🏠 New Home", data=f"act:disc:home:{platform}"),
                Button.inline("📈 Trending", data=f"act:disc:trending:{platform}")
            ],
            [Button.inline("⬅️ Back", data="back_start")]
        ]

    else:
        # Discovery buttons
        buttons = [
            [Button.inline("🔍 Search", data=f"act:search:query:{platform}")],
            [
                Button.inline("🏠 Home", data=f"act:disc:home:{platform}"),
                Button.inline("✨ Latest", data=f"act:disc:latest:{platform}")
            ],
            [
                Button.inline("🔥 For You", data=f"act:disc:foryou:{platform}"),
                Button.inline("🎙️ Dubbed", data=f"act:disc:dubbed:{platform}")
            ],
            [Button.inline("⬅️ Back", data="back_start")]
        ]
    
    text = (f"🎬 Platform: **{platform.upper()}**\n\n"
            f"🏠 Explore home content or search individually.")
    
    await event.edit(text, buttons=buttons)

@client.on(events.CallbackQuery(data=lambda d: d.startswith(b"act:")))
async def action_callback(event):
    await track_user(event)
    _, action, param, platform = event.data.decode().split(":")
    chat_id = event.chat_id
    
    if action == "search":
        user_states[chat_id] = {"platform": platform, "action": "search"}
        await event.edit(f"🔍 **SEARCH: {platform.upper()}**\nType drama name to search:", 
                         buttons=Button.inline("⬅️ Back", data=f"p:{platform}"))
    
    elif action == "disc":
        status = await event.respond(f"✨ Fetching {param} from {platform}...")
        try:
            prov = get_provider(platform)
            results = await prov.discover(param)
            if not results:
                return await status.edit(f"❌ No {param} content found on {platform}.")
            
            buttons = [[Button.inline(f"🎬 {res['title']}", data=f"d:{platform}:{res['id']}")] for res in results[:10]]
            buttons.append([Button.inline("⬅️ Back", data=f"p:{platform}")])
            
            await status.delete()
            await cleanup_last_msg(event.chat_id)
            msg_result = await event.respond(f"✅ **{param.upper()}** on **{platform.upper()}**:", buttons=buttons)
            user_states.setdefault(chat_id, {})["last_bot_msg"] = msg_result.id
        except Exception as e:
            import traceback
            error_details = traceback.format_exc()
            logger.error(f"Discovery Error ({platform}:{param}): {e}")
            
            admin_report = (f"🚨 **DISCOVERY ERROR**\n\n"
                           f"👤 **User**: `{event.chat_id}`\n"
                           f"📂 **Platform**: `{platform}`\n"
                           f"🧭 **Param**: `{param}`\n"
                           f"⚠️ **Error**: `{str(e)}`\n\n"
                           f"📋 **Traceback**:\n```{error_details[:3000]}```")
            await notify_admins(admin_report)
            await status.edit(f"❌ Discovery Error: {str(e)[:100]}")


@client.on(events.NewMessage())
async def message_handler(event):
    if event.text.startswith('/'): return
    await track_user(event)
    
    chat_id = event.chat_id
    state = user_states.get(chat_id, {})
    
    # Broadcast logic
    if state.get("action") == "broadcast_wait":
        if event.sender_id not in settings.admin_list: return
        user_ids = await db.get_all_users()
        sent = 0
        failed = 0
        status = await event.respond(f"📢 Starting broadcast to {len(user_ids)} users...")
        for uid in user_ids:
            try:
                await client.send_message(uid, event.message)
                sent += 1
            except: failed += 1
            if sent % 10 == 0: await status.edit(f"📢 Broadcast Progress: {sent}/{len(user_ids)}")
        
        await status.edit(f"✅ **Broadcast Finished!**\nSent: `{sent}`\nFailed: `{failed}`")
        user_states[chat_id] = {"action": "idle"}
        return

    if state.get("action") == "add_user_id":
        if event.sender_id not in settings.admin_list: return
        user_states[chat_id] = {"action": "add_user_dur", "target_id": event.text}
        await event.respond(f"✅ User ID: `{event.text}`\n\nMasukan durasi akses dalam hari (contoh: 30):")
        return

    if state.get("action") == "add_user_dur":
        if event.sender_id not in settings.admin_list: return
        try:
            days = int(event.text)
            target_id = int(user_states[chat_id]["target_id"])
            await db.add_authorized_user(target_id, days)
            await event.respond(f"✅ **Success!**\nUser: `{target_id}`\nDuration: `{days} days`\nAccess has been granted.")
            user_states[chat_id] = {"action": "idle"}
        except:
            await event.respond("❌ Error. Masukan angka yang valid untuk hari.")
        return

    if state.get("action") == "search":
        platform = state["platform"]
        msg = await event.respond("Searching...")
        try:
            prov = get_provider(platform)
            results = await prov.search(event.text)
            if not results: return await msg.edit("❌ No results found.")
            buttons = [[Button.inline(f"🎬 {res['title']}", data=f"d:{platform}:{res['id']}")] for res in results[:10]]
            await msg.delete()
            await cleanup_last_msg(event.chat_id)
            msg_result = await event.respond(f"✅ Results for **{platform.upper()}**:", buttons=buttons)
            user_states.setdefault(chat_id, {})["last_bot_msg"] = msg_result.id
            state["action"] = "idle"
        except Exception as e: await msg.edit(f"Error: {e}")

@client.on(events.CallbackQuery(data=lambda d: d.startswith(b"d:")))
async def detail_callback(event):
    await track_user(event)
    _, platform, drama_id = event.data.decode().split(":")
    chat_id = event.sender_id
    if not await db.is_authorized(chat_id): return await event.answer("⚠️ Access Denied", alert=True)

    status = await event.respond("🎨 Fetching details...")
    try:
        prov = get_provider(platform)
        details = await prov.get_drama_details(drama_id)
        
        title = details.get("title") or "Unknown Title"
        poster = details.get("poster")
        desc = details.get("description") or "No synopsis available."
        ep_count = details.get("total_episodes") or "Unknown"
        
        caption = (f"🎬 **{title}**\n\n"
                   f"🎞 Platform: `{platform.upper()}`\n"
                   f"📺 Total Episodes: `{ep_count}`\n\n"
                   f"📖 **Synopsis**:\n{desc[:800]}...")
        
        buttons = [
            [Button.inline("🚀 Download Full Drama", data=f"dl:{platform}:{drama_id}")],
            [Button.inline("⬅️ Back to Search", data=f"p:{platform}")]
        ]

        await status.edit("🪄 **Uploading Details...**")
        try:
            if poster and str(poster).startswith("http"):
                await event.respond(caption, file=poster, buttons=buttons)
            else:
                await event.respond(caption, buttons=buttons)
            await status.delete()
        except Exception as upload_err:
            logger.error(f"Poster Upload Error: {upload_err}")
            await event.respond(caption, buttons=buttons)
            await status.delete()
            
    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        logger.error(f"Detail Fetch Error: {e}")
        
        admin_report = (f"🚨 **DETAIL FETCH ERROR**\n\n"
                       f"👤 **User**: `{event.chat_id}`\n"
                       f"🆔 **ID**: `{drama_id}`\n"
                       f"⚠️ **Error**: `{str(e)}`\n\n"
                       f"📋 **Traceback**:\n```{error_details[:3000]}```")
        await notify_admins(admin_report)
        
        try: await status.edit(f"❌ Detail Error: {str(e)[:100]}")
        except: await event.respond(f"❌ Error: {str(e)[:100]}")


@client.on(events.CallbackQuery(data=lambda d: d.startswith(b"dl:")))
async def download_callback(event):
    await track_user(event)
    _, platform, drama_id = event.data.decode().split(":")
    chat_id = event.chat_id
    if not await db.is_authorized(chat_id): return await event.answer("⚠️ Access Denied", alert=True)

    await event.answer("📥 Added to queue...", alert=False)
    
    # Track position in queue
    pos = worker.pending_count + 1
    status_msg = await event.respond(f"⏳ **QUEUE POSITION #{pos}**\nPreparing `{drama_id}` from {platform}...", 
                                    buttons=[Button.inline("⏹️ Cancel Task", data=f"cancel_dl:{chat_id}")])

    async def process_task():
        temp_files = []
        try:
            last_edit_time = 0
            start_time = time.time()
            
            async def edit_throttled(text):
                nonlocal last_edit_time
                if time.time() - last_edit_time > 2.2:
                    try: 
                        await status_msg.edit(text, buttons=[Button.inline("⏹️ Cancel Task", data=f"cancel_dl:{chat_id}")])
                        last_edit_time = time.time()
                    except: pass

            prov = get_provider(platform)
            await edit_throttled(f"🎬 Starting processing `{drama_id}`...")
            
            # Fetch details for proper captioning
            details = await prov.get_drama_details(drama_id)
            drama_title = details.get("title") or drama_id
            
            episodes = await prov.get_episodes(drama_id)
            if not episodes: raise Exception("No episodes found.")
            for i, ep in enumerate(episodes, 1):
                # Try to use URL from episode object first to avoid extra requests
                stream_url = ep.get('stream_url') or await prov.get_stream_url(drama_id, i)
                
                if stream_url:
                    dest = os.path.join(settings.download_dir, f"{drama_id}_ep{i}.mp4")
                    
                    async def progress_cb(percent, current_s, total_s):
                        elapsed = time.time() - start_time
                        speed = (current_s / elapsed) if elapsed > 0 else 0
                        eta = (total_s - current_s) / speed if speed > 0 else 0
                        bar = processor.generate_progress_bar(percent)
                        # Download progress
                        text = (f"🟢 **Downloading Ep {i}/{len(episodes)}**\n"
                                f"{bar}\n"
                                f"⚡ Speed: {speed:.1f}x\n"
                                f"⏱️ ETA: {int(eta // 60)}m {int(eta % 60)}s\n"
                                f"📊 Queue: {worker.pending_count} left")
                        await edit_throttled(text)

                    await processor.download_video(stream_url, dest, progress_cb, video_key=ep.get('video_key'))
                    temp_files.append(dest)
                else:
                    logger.warning(f"No stream URL for Ep {i}")

            if not temp_files:
                raise Exception("Gagal mengunduh semua episode (URL tidak ditemukan).")

            # Create a safe file name from title
            safe_title = "".join([c if c.isalnum() else "_" for c in drama_title])[:50]
            await status_msg.edit("⚙️ **Merging episodes...**")
            output_file = os.path.join(settings.download_dir, f"{safe_title}_merged.mp4")
            
            async def merge_cb(percent, current_s, total_s):
                bar = processor.generate_progress_bar(percent)
                await edit_throttled(f"⚙️ **Merging Episodes**\n{bar}\n📊 Persentase: {percent:.1f}%")

            await processor.merge_videos(temp_files, output_file, len(episodes), on_progress=merge_cb)

            await status_msg.edit("🪄 **Uploading to Telegram...**")
            
            async def upload_cb(current, total):
                percent = (current / total) * 100
                bar = processor.generate_progress_bar(percent)
                await edit_throttled(f"🪄 **Uploading Final File**\n{bar}\n📊 Persentase: {percent:.1f}%")

            # Append soft-sub note if it's FreeReels or similar
            sub_note = "\n\nℹ️ _Subtitle sudah menyatu dalam video (Soft Sub)_" if platform == "freereels" else ""
            await uploader.upload_file(chat_id, output_file, caption=f"[{platform.upper()}] {drama_title}{sub_note}", progress_callback=upload_cb)
            await status_msg.delete()
            
        except asyncio.CancelledError:
            logger.warning(f"Task cancelled by user {chat_id}")
            await status_msg.edit("🛑 **Task Cancelled by User.**")
        except Exception as e:
            import traceback
            error_details = traceback.format_exc()
            logger.exception(f"Download Error for {chat_id}")
            
            # User Feedback
            try: await status_msg.edit(f"❌ **Error Occurred.**\nAdmin has been notified.")
            except: pass
            
            # Admin Notification
            admin_report = (f"🚨 **BOT ERROR REPORT**\n\n"
                           f"👤 **User**: `{chat_id}`\n"
                           f"📂 **Platform**: `{platform}`\n"
                           f"🆔 **Drama ID**: `{drama_id}`\n"
                           f"⚠️ **Error**: `{str(e)}`\n\n"
                           f"📋 **Traceback**:\n```{error_details[:3000]}```")
            await notify_admins(admin_report)

        finally:
            # Cleanup all temp files
            logger.info(f"Cleanup: {len(temp_files)} files for {chat_id}")
            for f in temp_files:
                if os.path.exists(f): 
                    try: os.remove(f)
                    except: pass
            user_states[chat_id] = {"action": "idle"}

    # Start the processing task in background via queue
    await worker.add_task(chat_id, process_task)

@client.on(events.CallbackQuery(data=lambda d: d.startswith(b"cancel_dl:")))
async def cancel_dl_callback(event):
    chat_id = int(event.data.decode().split(":")[1])
    if event.sender_id != chat_id and event.sender_id not in settings.admin_list:
        return await event.answer("❌ You cannot cancel this task.", alert=True)
    
    ok = await worker.cancel_task(chat_id)
    if ok:
        await event.answer("🛑 Cancelling task...", alert=True)
    else:
        await event.answer("⚠️ Task already finished or not running.", alert=True)

@client.on(events.CallbackQuery(data=b"back_start"))
async def back_handler(event): 
    await track_user(event)
    buttons, cur, total = await build_platform_buttons(event.sender_id)
    await event.edit(f"🎬 **Drama Automation Bot**\nSelect your platform:\n\nPage: `{cur}/{total}`", buttons=buttons)

def cleanup_downloads():
    if not os.path.exists(settings.download_dir):
        os.makedirs(settings.download_dir)
        return
    logger.info("Cleaning up downloads directory at startup...")
    for f in os.listdir(settings.download_dir):
        path = os.path.join(settings.download_dir, f)
        try:
            if os.path.isfile(path): os.remove(path)
        except: pass
    # Clean up concat files and sessions in root
    for f in os.listdir('.'):
        if (f.startswith('concat_') and f.endswith('.txt')) or f.endswith('.session') or f.endswith('.session-journal'):
            try: 
                os.chmod(f, 0o777)
                os.remove(f)
                logger.info(f"Auto-cleaned session file: {f}")
            except: pass


async def main():
    await db.init()
    cleanup_downloads()
    # Start Client with TOTAL Session recovery
    session_file = 'drama_bot_session.session'
    try:
        await client.start(bot_token=settings.bot_token)
    except Exception as e:
        err_msg = str(e).lower()
        if "readonly" in err_msg or "locked" in err_msg:
            logger.warning(f"Session database error detected: {e}")
            try: await client.disconnect()
            except: pass
            
            # Action: Clean up file
            did_remove = False
            if os.path.exists(session_file):
                try:
                    os.chmod(session_file, 0o777)
                    os.remove(session_file)
                    logger.info(f"Cleaned up {session_file}")
                    did_remove = True
                except: pass
            
            # Anti-Loop: Only reboot if we cleaned something OR if file still exists
            if os.path.exists(session_file) or did_remove:
                logger.info("Rebooting bot for fresh session...")
                os.execl(sys.executable, sys.executable, *sys.argv)
            else:
                logger.critical("FATAL: Directory is Read-Only. Bot cannot start.")
                sys.exit(1)
        else:
            raise e



    worker.start()
    logger.info("Bot is running (Python Enhanced)")
    await client.run_until_disconnected()

if __name__ == '__main__':
    import asyncio
    asyncio.run(main())
