const { default: PQueue } = require('p-queue');
const config = require('../config');

class QueueManager {
    constructor() {
        this.queue = new PQueue({ concurrency: config.maxConcurrent });
        this.pendingCount = 0;
    }

    async add(task) {
        return this.queue.add(async () => {
            try {
                await task();
            } finally {
                // Task finished
            }
        });
    }

    get stats() {
        return {
            size: this.queue.size,
            pending: this.queue.pending,
            total: this.queue.size + this.queue.pending
        };
    }
}

module.exports = new QueueManager();
