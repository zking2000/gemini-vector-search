import React from 'react';
import { useTranslation } from 'react-i18next';
import { Select } from 'antd';
import { GlobalOutlined } from '@ant-design/icons';

const LanguageSwitcher = () => {
  const { i18n } = useTranslation();
  
  const handleChange = (value) => {
    i18n.changeLanguage(value);
  };
  
  return (
    <div className="language-switcher">
      <Select
        defaultValue={i18n.language}
        style={{ width: 100 }}
        onChange={handleChange}
        suffixIcon={<GlobalOutlined />}
        options={[
          { value: 'zh', label: '中文' },
          { value: 'en', label: 'English' }
        ]}
      />
    </div>
  );
};

export default LanguageSwitcher; 