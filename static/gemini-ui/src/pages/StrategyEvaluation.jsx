import React, { useState } from 'react';
import { Typography, Spin } from 'antd';
import { useTranslation } from 'react-i18next';

const { Title } = Typography;

const StrategyEvaluation = () => {
  const { t, i18n } = useTranslation();
  const [loading, setLoading] = useState(true);

  // 处理iframe加载完成事件
  const handleIframeLoad = () => {
    setLoading(false);
  };

  // 根据当前语言选择报告文件
  const reportFile = i18n.language === 'zh' ? 'benchmark_zh.html' : 'benchmark_en.html';

  return (
    <div className="strategy-evaluation-container">
      <Title level={2} style={{ marginBottom: 20 }}>{t('nav.strategyEvaluation')}</Title>
      
      {loading && (
        <div style={{ textAlign: 'center', padding: '40px 0' }}>
          <Spin size="large" tip={t('common.loading')} />
        </div>
      )}
      
      <div style={{ position: 'relative', height: 'calc(100vh - 250px)', width: '100%', overflow: 'hidden' }}>
        <iframe 
          src={`/report/${reportFile}`}
          style={{ 
            border: 'none', 
            width: '100%', 
            height: '100%',
            display: loading ? 'none' : 'block'
          }}
          title={t('nav.strategyEvaluation')}
          onLoad={handleIframeLoad}
        />
      </div>
    </div>
  );
};

export default StrategyEvaluation; 