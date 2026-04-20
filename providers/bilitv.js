const BaseProvider = require('./base');
const config = require('../config');

class BiliTVProvider extends BaseProvider {
    constructor() {
        super();
        this.baseUrl = 'https://bilitv.dramabos.my.id/api';
    }

    async search(query) {
        try {
            const res = await this.get(`${this.baseUrl}/search`, { q: query, lang: 'id' });
            const results = Array.isArray(res.data) ? res.data : (res.data.data || []);
            return results.filter(i => typeof i === 'object').map(item => ({
                id: String(item.id),
                title: item.title || item.name || 'No Title',
                platform: 'bilitv'
            }));
        } catch (e) {
            console.error('BiliTV Search Error:', e.message);
            return [];
        }
    }

    async getEpisodes(dramaId) {
        try {
            const res = await this.get(`${this.baseUrl}/short/${dramaId}/episode`);
            const episodes = Array.isArray(res.data) ? res.data : (res.data.data || []);
            return episodes.map(ep => ({
                id: String(ep.id),
                number: ep.episode_no || ep.number,
                title: `Episode ${ep.episode_no || ep.number}`
            }));
        } catch (e) {
            console.error('BiliTV Episodes Error:', e.message);
            return [];
        }
    }

    async getStreamUrl(dramaId, epNo = 1) {
        try {
            const res = await this.get(`${this.baseUrl}/stream/${dramaId}/${epNo}`, {
                quality: '720',
                lang: 'id',
                code: config.tokenDramabos
            });
            return res.data.url || (res.data.data && res.data.data.url);
        } catch (e) {
            console.error('BiliTV Stream Error:', e.message);
            return null;
        }
    }
}

module.exports = BiliTVProvider;
