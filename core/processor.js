const ffmpeg = require('fluent-ffmpeg');
const config = require('../config');
const fs = require('fs');
const path = require('path');
const { exec } = require('child_process');
const util = require('util');
const execAsync = util.promisify(exec);

ffmpeg.setFfmpegPath(config.ffmpegPath);

class VideoProcessor {
    async downloadVideo(url, destPath, onProgress) {
        return new Promise((resolve, reject) => {
            let duration = 0;
            
            ffmpeg(url)
                .outputOptions([
                    '-c copy',
                    '-bsf:a aac_adtstoasc'
                ])
                .on('start', (command) => {
                    console.log('Ffmpeg started:', command);
                })
                .on('codecData', (data) => {
                    // Extract duration if possible
                    if (data.duration) {
                        const parts = data.duration.split(':');
                        duration = (+parts[0]) * 3600 + (+parts[1]) * 60 + (+parts[2]);
                    }
                })
                .on('progress', (progress) => {
                    if (onProgress && duration > 0) {
                        const timemarkParts = progress.timemark.split(':');
                        const seconds = (+timemarkParts[0]) * 3600 + (+timemarkParts[1]) * 60 + (+timemarkParts[2]);
                        const percent = Math.min(100, (seconds / duration) * 100);
                        
                        onProgress({
                            percent,
                            speed: progress.currentKbps,
                            timemark: progress.timemark
                        });
                    }
                })
                .on('error', (err) => {
                    reject(err);
                })
                .on('end', () => {
                    resolve();
                })
                .save(destPath);
        });
    }

    async mergeVideos(inputFiles, outputFile, onProgress) {
        // Concat logic using fluent-ffmpeg
        return new Promise((resolve, reject) => {
            const command = ffmpeg();
            
            inputFiles.forEach(file => {
                command.input(path.resolve(file));
            });

            command
                .on('error', reject)
                .on('end', resolve)
                .on('progress', onProgress)
                .mergeToFile(outputFile, path.dirname(outputFile));
        });
    }

    generateProgressBar(percent, length = 15) {
        const filledLength = Math.round((percent / 100) * length);
        const bar = '█'.repeat(filledLength) + '░'.repeat(length - filledLength);
        return `[${bar}] ${percent.toFixed(1)}%`;
    }
}

module.exports = new VideoProcessor();
