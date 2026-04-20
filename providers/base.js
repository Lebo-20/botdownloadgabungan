const axios = require('axios');
const config = require('../config');

class BaseProvider {
    constructor() {
        this.client = axios.create({
            timeout: 30000,
            headers: {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
            }
        });
    }

    async get(url, params = {}, headers = {}) {
        return this.client.get(url, { params, headers });
    }
}

module.exports = BaseProvider;
