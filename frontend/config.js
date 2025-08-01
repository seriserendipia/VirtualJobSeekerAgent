// 服务器配置管理
const SERVER_CONFIG = {
    LOCAL: "http://localhost:5000",
    RAILWAY: "https://virtualjobseekeragent-production.up.railway.app",  // 预测的Railway URL
    CURRENT: "RAILWAY"  // 直接切换到云端模式
};

// 获取当前服务器地址
function getServerUrl() {
    return SERVER_CONFIG[SERVER_CONFIG.CURRENT];
}

// 导出配置 (如果需要)
if (typeof module !== 'undefined' && module.exports) {
    module.exports = { SERVER_CONFIG, getServerUrl };
}
