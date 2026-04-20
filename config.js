require('dotenv').config();

const config = {
    telegramToken: process.env.BOT_TOKEN,
    adminIds: (process.env.ADMIN_IDS || '').split(',').filter(x => x).map(Number),
    downloadDir: process.env.DOWNLOAD_DIR || 'downloads',
    ffmpegPath: process.env.FFMPEG_PATH || 'ffmpeg',
    aria2cPath: process.env.ARIA2C_PATH || 'aria2c',
    tokenDramabos: process.env.TOKEN_DRAMABOS,
    tokenSapimu: process.env.TOKEN_SAPIMU,
    maxConcurrent: 2
};

module.exports = config;
