根据你上传的 GPFG Annual Report 2023 年报内容（你已做过 chunking 并用于 RAG），我为你设计了几组用于测试集成查询功能的典型问题，覆盖财务数据、投资结构、策略评估等关键主题，便于测试你的系统在不同类型信息上的回答能力。

⸻

🧪 推荐测试问题设计（含难度与意图）：

📊 投资回报类（数字/对比查询）
	1.	What was the total return of the Government Pension Fund Global in 2023, and how did it compare to the benchmark index?
检测数字提取与相对回报对比
	2.	What was the return on unlisted real estate investments in 2023?
检查负收益提取与资产类型识别
	3.	How much did the fund’s market value increase in 2023 and what factors contributed to it?
复合型问题：要求理解数字增长+解释原因
	4.	Which asset class had the highest return in 2023 and why?
测试系统是否能提取 Tech stocks 及其背景

⸻

🧱 资产结构类（结构化数据提取）
	5.	What was the asset allocation of the fund at the end of 2023?
提取：Equity, Fixed Income, Real Estate, Renewable Energy 的比例
	6.	How much of the fund was invested in US equities and bonds at the end of 2023?
跨表格结构的国家+资产类型提取
	7.	What percentage of the real estate investments was allocated to office properties?
用于测试对图表和分布文字的 chunk 理解

⸻

🎯 策略与管理类（概念性 + 分析型问题）
	8.	What are the three main investment strategies used by Norges Bank to manage the fund?
测试系统是否能提取 market exposure / security selection / fund allocation
	9.	Why did unlisted real estate investments underperform in 2023?
结合多段文字解释：利率上升、办公需求下降等
	10.	What is the role of responsible investment in the fund’s strategy, and how is it implemented?
适合测试 ESG 或 AI 观点的支持情况

⸻

⚠️ 风险与压力测试类
	11.	What are the key risks identified in the 2023 stress tests, and what potential losses were estimated?
期望提取 “Debt crisis”、“Divided world”、“Repricing of risk” 三种情景及对应损失
	12.	What is the expected absolute volatility of the fund as of 2023, and what does it imply?
考察波动率数值与实际影响解释

⸻

🔁 长期绩效类
	13.	What was the average annual return of the fund from 1998 to 2023?
	14.	How did equity and fixed-income management contribute to relative return over the past 5 years?