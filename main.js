const { Telegraf, Markup } = require('telegraf');
const config = require('./config');
const queue = require('./core/queueManager');
const processor = require('./core/processor');
const BiliTVProvider = require('./providers/bilitv');
const fs = require('fs');
const path = require('path');

const bot = new Telegraf(config.telegramToken);
const providers = {
    bilitv: new BiliTVProvider()
};

// State
const userStates = new Map();

bot.start((ctx) => {
    ctx.reply('🎬 **Drama Automation Bot (Node.js)**\n\nSilakan pilih platform:', Markup.inlineKeyboard([
        [Markup.button.callback('BILITV', 'p:bilitv')]
    ]));
});

bot.action(/p:(.+)/, async (ctx) => {
    const platform = ctx.match[1];
    userStates.set(ctx.chat.id, { platform, action: 'search' });
    await ctx.answerCbQuery();
    await ctx.editMessageText(`🔍 Platform: **${platform.toUpperCase()}**\n\nKetik nama drama:`, Markup.inlineKeyboard([
        [Markup.button.callback('⬅️ Kembali', 'back')]
    ]));
});

bot.action('back', async (ctx) => {
    await ctx.editMessageText('🎬 Silakan pilih platform:', Markup.inlineKeyboard([
        [Markup.button.callback('BILITV', 'p:bilitv')]
    ]));
});

bot.on('text', async (ctx) => {
    const state = userStates.get(ctx.chat.id);
    if (!state || state.action !== 'search') return;

    const query = ctx.message.text;
    const provider = providers[state.platform];
    const status = await ctx.reply(`Searching \`${query}\`...`);

    try {
        const results = await provider.search(query);
        if (!results.length) return ctx.reply('❌ Tidak ditemukan.');

        const buttons = results.slice(0, 10).map(res => [
            Markup.button.callback(`📥 ${res.title}`, `d:${state.platform}:${res.id}`)
        ]);
        
        await ctx.telegram.deleteMessage(ctx.chat.id, status.message_id);
        await ctx.reply(`✅ Hasil untuk **${state.platform.toUpperCase()}**:`, Markup.inlineKeyboard(buttons));
        state.action = 'idle';
    } catch (e) {
        await ctx.reply(`Error: ${e.message}`);
    }
});

bot.action(/d:(.+):(.+)/, async (ctx) => {
    const platform = ctx.match[1];
    const dramaId = ctx.match[2];
    
    if (!config.adminIds.includes(ctx.chat.id)) {
        return ctx.answerCbQuery('⚠️ Admin Only', { show_alert: true });
    }

    await ctx.answerCbQuery('📥 Diproses...');
    const status = await ctx.reply(`⏳ Menunggu antrian...`);

    // Task for the queue
    const task = async () => {
        try {
            const provider = providers[platform];
            await ctx.telegram.editMessageText(ctx.chat.id, status.message_id, null, `🎬 Memulai proses drama \`${dramaId}\`...`);
            
            const episodes = await provider.getEpisodes(dramaId);
            const tempFiles = [];
            
            let lastUpdate = Date.now();
            
            for (let i = 0; i < episodes.length; i++) {
                const ep = episodes[i];
                const streamUrl = await provider.getStreamUrl(dramaId, i + 1);
                
                if (streamUrl) {
                    const destPath = path.join(config.downloadDir, `ep_${dramaId}_${i+1}.mp4`);
                    
                    await processor.downloadVideo(streamUrl, destPath, (p) => {
                        const now = Date.now();
                        if (now - lastUpdate > 2000) {
                            lastUpdate = now;
                            const bar = processor.generateProgressBar(p.percent);
                            const text = `📥 **Mengunduh Ep ${i+1}/${episodes.length}**\n${bar}\nSpeed: ${p.speed} kbps\nETA: ${p.timemark}\n\nQueue: ${queue.stats.total}`;
                            ctx.telegram.editMessageText(ctx.chat.id, status.message_id, null, text).catch(() => {});
                        }
                    });
                    tempFiles.append(destPath);
                }
            }

            await ctx.telegram.editMessageText(ctx.chat.id, status.message_id, null, `⚙️ Merging ${tempFiles.length} files...`);
            const outputFile = path.join(config.downloadDir, `merged_${dramaId}.mp4`);
            await processor.mergeVideos(tempFiles, outputFile);

            await ctx.telegram.editMessageText(ctx.chat.id, status.message_id, null, `📤 Uploading...`);
            await ctx.replyWithVideo({ source: outputFile }, { caption: `Drama: ${dramaId}` });
            
            // Cleanup
            tempFiles.forEach(f => fs.unlinkSync(f));
            fs.unlinkSync(outputFile);
            await ctx.telegram.deleteMessage(ctx.chat.id, status.message_id);

        } catch (e) {
            console.error(e);
            await ctx.telegram.editMessageText(ctx.chat.id, status.message_id, null, `❌ Gagal: ${e.message}`);
        }
    };

    queue.add(task);
    const stats = queue.stats;
    await ctx.telegram.editMessageText(ctx.chat.id, status.message_id, null, `⏳ Antrian #${stats.total}\nConcurrent: ${stats.pending}/${config.maxConcurrent}`);
});

bot.launch().then(() => console.log('Bot is running (Node.js)'));

process.once('SIGINT', () => bot.stop('SIGINT'));
process.once('SIGTERM', () => bot.stop('SIGTERM'));
