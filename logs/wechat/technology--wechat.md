---
title: "AI Agent 落地：从自动化到可控工作流"
date: "2026-02-26T18:18:14+08:00"
draft: false
categories: ["technology"]
tags: ["technology", "news", "AI分析"]
author: "AI智汇观察"
slug: "technology-"
image: "/images/posts/technology-/cover.jpg"
---
![封面图](/images/posts/technology-/cover.jpg)

---

【核心摘要】

---

1. 【成本与效率驱动架构变革】：面对每日高达80亿次的Token使用量，AT&T通过重构编排层，采用“超级智能体”指挥小型“工作智能体”的多智能体架构，实现了高达90%的成本节约和显著的延迟改善[1]。
2. 【模型格局向小型化与开源演进】：阿里云开源了具备智能体工具调用能力的Qwen3.5 Medium系列模型，其性能可比肩顶级闭源模型，为企业本地化部署提供了高性能、低成本的选择[4]。同时，行业领军者认为未来将由大量小型语言模型（SLMs）驱动[1]。
3. 【应用层创新与商业模式冲击并存】：初创公司如Gushwork正利用AI搜索重塑客户线索获取方式[9]，而AI智能体的崛起也引发了市场对传统SaaS按席位收费商业模式的“SaaSpocalypse”担忧[6]。
4. 【基础设施与伦理成为关键变量】：全球内存短缺导致硬件成本飙升，直接影响AI部署的经济性[5]；同时，AI公司正面临是否应将其技术用于军事监控等伦理原则的严峻考验[8]。

---

【今日要点】

---

一、 架构革命：从“大模型通吃”到“分层智能体协作”

AI智能体落地的首要挑战，从技术可行性转向了经济可行性与规模化效率。AT&T的案例极具代表性：当每日的Token消耗量达到【80亿次】时，将所有任务都推送给大型推理模型变得既不现实也不经济[1]。

其解决方案是彻底重构智能体编排层，构建了一个基于LangChain的多智能体堆栈。在这个架构中，大型语言模型扮演“超级智能体”的角色，负责高层级的规划和决策；它们指挥下层众多小型、专用的“工作智能体”去执行具体、目标明确的任务[1]。这种分工带来了立竿见影的效果：延迟、速度和响应时间得到显著改善，最关键的是实现了【高达90%的成本节约】[1]。

AT&T首席数据官Andy Markus的观点指明了方向：“我相信智能体AI的未来是【非常多、非常多、非常多的小型语言模型（SLMs）】。我们发现在特定领域，小型语言模型的准确度与大型语言模型相当，甚至更优。”[1] 这一架构思想已产品化，其团队利用微软Azure构建并部署了“Ask AT&T Workflows”，一个图形化的拖放式智能体构建器，供员工自动化任务[1]。

二、 模型生态：开源高性能模型加速企业级部署

智能体架构的演进，离不开底层模型能力的支持。阿里云Qwen AI团队最新开源的Qwen3.5 Medium模型系列，为企业构建可控工作流提供了强大的基础工具。该系列包含多个模型，其中三个（Qwen3.5-35B-A3B, Qwen3.5-122B-A10B, Qwen3.5-27B）在标准的Apache 2.0开源协议下可供企业和独立开发者商业使用[4]。

这些模型的关键特性在于支持【智能体工具调用】，并且其性能宣称可媲美Anthropic的顶级闭源模型Sonnet 4.5，同时能在本地计算机上运行[4]。此外，阿里云还通过Model Studio API提供了一个专有模型Qwen3.5-Flash，与其他西方模型相比在成本上具有优势[4]。高性能开源模型的涌现，降低了企业构建和实验专属智能体工作流的门槛，使得AT&T所倡导的“SLMs”策略更具可操作性。

三、 应用前沿：智能体重塑获客与工作界面

在应用层面，AI智能体正在创造新的商业机会并重新定义人机交互。

在商业获客领域，初创公司Gushwork看到了AI搜索工具（如ChatGPT、Gemini、Perplexity）重塑企业线上被发现方式的趋势。它通过自动化营销智能体，帮助企业从这些新兴的AI驱动发现渠道中捕获客户线索[9]。这一早期尝试已获得资本认可，该公司近期完成了900万美元的种子轮融资，投后估值达到3300万美元[9]。

另一方面，智能体技术开始深入渗透到核心工作界面。 Anthropic近期收购了计算机使用AI初创公司Vercept，后者开发了名为Vy的云端智能体，可以远程操作苹果MacBook[10]。这代表了行业对“为AI智能体时代重新构想个人计算机”方向的押注[10]。此前，Anthropic已在2025年12月收购了编码智能体引擎Bun，以扩展其Claude Code的能力[10]。这些收购表明，领先的AI公司正通过整合垂直能力，构建能够理解并操作复杂数字环境的全能型智能体。

四、 外部约束：硬件成本与伦理原则的挑战

AI智能体的规模化落地并非纯粹的技术问题，同样受到外部环境的强烈制约。

首先，硬件成本正成为一个突出的瓶颈。全球内存短缺导致DRAM和NAND价格飙升。以HP为例，其PC产品中内存占物料成本（BOM）的比例，已从2025财年第四季度的约【15%至18%】，飙升至本财年（2026财年）剩余时间的约【35%】[5]。HP首席财务官表示，内存成本已环比上涨约【100%】，且预计在财年内将进一步上涨[5]。这对于需要大量本地计算资源的智能体部署而言，无疑增加了经济负担。

其次，AI公司正面临严峻的伦理与政治压力。据报道，美国国防部长已向Anthropic发出最后通牒，试图迫使其取消对技术使用的限制，使其可供美军无限制使用，包括用于其公开声明中反对的【自主武器系统和监控】领域[8]。国防部甚至威胁将Anthropic列为“供应链风险”企业[8]。这迫使AI公司必须在商业机会、国家压力与自我设定的伦理原则之间做出艰难抉择。

---

【数据与指标】

---

![封面图](/images/default-cover.png)
图1：封面图
图片来源：自制封面图（AI智汇观察）

成本与效率指标

* 【规模化运营成本】：AT&T通过采用多智能体分层架构，将大规模AI任务处理的成本降低了【90%】[1]。
* 【资源消耗规模】：在架构优化前，AT&T的AI系统日均Token使用量高达【80亿次】，凸显了超大规模企业部署面临的成本挑战[1]。
* 【硬件成本波动】：全球内存短缺导致PC内存成本在短期内环比上涨约【100%】，使其在整机物料成本中的占比从约15-18%跃升至约【35%】[5]。

市场与资本指标

* 【初创企业估值】：专注于AI搜索获客的初创公司Gushwork在完成900万美元种子轮融资后，投后估值达到【3300万美元】，较其2023年7月750万美元的估值大幅增长[9]。
* 【SaaS巨头营收】：作为SaaS行业的代表，Salesforce在2026财年第四季度营收为【107亿美元】，同比增长13%；全年营收为【415亿美元】，同比增长10%[6]。其未履约性能义务（RPO）超过【720亿美元】，显示了庞大的存量合同规模[6]。
* 【融资规模】：Gushwork本轮种子轮融资金额为【900万美元】，领投方为SIG和Lightspeed，使其总融资额达到【1100万美元】[9]。

---

【影响与机会】

---

给企业的建议

1. 【优先重构架构，而非单纯追求大模型】：借鉴AT&T的实践，企业应评估自身AI任务流，探索采用“超级智能体+专用工作智能体”的分层协作架构。这能有效控制随着使用量激增而失控的推理成本，是实现AI规模化、可持续应用的关键第一步[1]。
2. 【积极评估并采用高性能开源模型】：密切关注如阿里云Qwen系列等高性能开源模型的发展[4]。它们为企业构建和微调专属领域智能体提供了成本更低、可控性更强的选择，有助于将AI能力深度嵌入到核心工作流程中。
3. 【将硬件成本纳入AI部署的长期规划】：当前内存等硬件的成本高企且波动剧烈[5]。企业在规划本地化或边缘AI智能体部署时，需进行更审慎的总体拥有成本（TCO）测算，并考虑混合云策略以平衡性能与成本。

给从业者（开发者、产品经理）的建议

1. 【掌握智能体编排与SLMs技能】：未来的核心竞争力在于如何将复杂的业务逻辑分解为可由多个小型、高效模型协同完成的工作流。深入学习LangChain等编排框架，并熟悉不同规模模型（尤其是SLMs）的特性与调优方法，变得至关重要[1][4]。
2. 【聚焦“AI原生”应用场景创新】：像Gushwork利用AI搜索重塑获客[9]，或Vercept探索计算机使用智能体[10]这样的方向，代表了真正的“AI原生”机会。从业者应跳出对传统流程的简单自动化，思考AI智能体如何从根本上改变信息获取、软件交互乃至工作界面的形态。
3. 【关注人机协同与可控性设计】：智能体越强大，确保其行为符合预期、过程可控透明就越重要。产品设计需重点考虑如何让人类有效监督、干预和修正智能体工作流，构建可靠的人机协同循环。

给投资者的建议

1. 【识别赋能“可控工作流”的底层工具】：投资机会不仅在于应用层智能体，更在于支撑智能体可靠、高效、低成本运行的“铲子”：包括智能体编排平台、针对SLMs的优化与部署工具、以及提升智能体可靠性的评估与监控方案。
2. 【重新评估SaaS投资逻辑】：市场对“SaaSpocalypse”的担忧反映了AI智能体对传统软件商业模式的潜在颠覆[6]。投资者需仔细甄别哪些SaaS公司能真正将AI智能体转化为增强其产品护城河的工具（如Salesforce正在尝试的），而哪些公司的商业模式可能被更灵活、更廉价的智能体工作流所解构。
3. 【警惕技术之外的重大风险】：投资AI公司时，需将其【伦理立场】和可能面临的【政治压力】纳入风险评估框架。如Anthropic所面临的军方压力事件表明，这类非商业风险可能对公司的技术路线、合作伙伴关系乃至长期生存产生决定性影响[8]。

---
来源列表

[1] 8 billion tokens a day forced AT&T to rethink AI orchestration — and cut costs by 90% - https://venturebeat.com/orchestration/8-billion-tokens-a-day-forced-at-and-t-to-rethink-ai-orchestration-and-cut
[2] TurboTax Service Codes: Up to 20% Off - https://www.wired.com/story/turbotax-coupon/
[3] Paramount Plus Coupon Codes and Deals: 50% Off - https://www.wired.com/story/paramount-plus-coupon-code/
[4] Alibaba's new open source Qwen3.5-Medium models offer Sonnet 4.5 performance on local computers - https://venturebeat.com/technology/alibabas-new-open-source-qwen3-5-medium-models-offer-sonnet-4-5-performance
[5] RAM now represents 35 percent of bill of materials for HP PCs - https://arstechnica.com/gadgets/2026/02/ram-now-represents-35-percent-of-bill-of-materials-for-hp-pcs/
[6] Salesforce CEO Marc Benioff: This isn't our first SaaSpocalypse - https://techcrunch.com/2026/02/25/salesforce-ceo-marc-benioff-this-isnt-our-first-saaspocalypse/
[7] Zyora-Dev/zse: Zyora Server Inference Engine for LLM . - https://github.com/Zyora-Dev/zse
[8] Tech Companies Shouldn’t Be Bullied Into Doing Surveillance - https://www.eff.org/deeplinks/2026/02/tech-companies-shouldnt-be-bullied-doing-surveillance
[9] Gushwork bets on AI search for customer leads - and early results are emerging - https://techcrunch.com/2026/02/25/gushwork-bets-on-ai-search-for-customer-leads-and-early-results-are-emerging/
[10] Anthropic acquires computer-use AI startup Vercept after Meta poached one of its founders - https://techcrunch.com/2026/02/25/anthropic-acquires-vercept-ai-startup-agents-computer-use-founders-investors/

---
本文由AI智汇观察系统自动生成
生成时间：2026年02月26日 10:18
数据来源：文中已标注
使用建议：数据仅供参考，投资需谨慎

关注「AI智汇观察」获取最新行业分析