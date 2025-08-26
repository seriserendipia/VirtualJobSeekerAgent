// 服务器配置管理模板
const SERVER_CONFIG = {
    LOCAL: "http://127.0.0.1:5000",
    RAILWAY: "https://virtualjobseekeragent-production.up.railway.app",
    // 开发时使用LOCAL，部署时使用RAILWAY
    CURRENT: "RAILWAY" // 构建时替换的占位符
};

// 获取当前服务器地址
function getServerUrl() {
    return SERVER_CONFIG[SERVER_CONFIG.CURRENT];
}

// 导出配置 (如果需要)
if (typeof module !== 'undefined' && module.exports) {
    module.exports = { SERVER_CONFIG, getServerUrl };
}
