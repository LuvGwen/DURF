# DURF Werewolf Simulation 中文汇报稿

## Slide 1 — Deception, Credibility, and Search Under Hidden Information

### 建议讲稿
大家好，今天我汇报 DURF Werewolf Simulation 的完整研究进展。这个项目用狼人杀作为一个可控实验环境，研究隐藏信息、欺骗、可信度和顺序信息搜索。整份报告的主线是：先建立可运行 baseline，再逐步加入信息机制和行为机制，最后把研究问题推进到“有限信息下，agent 应该怎样搜索最有价值的信息”。

### 本页核心信息
这是一个用狼人杀研究隐藏信息决策的模拟实验项目。

### 转场
先说明为什么狼人杀适合作为研究环境。

## Slide 2 — Werewolf is a compact model of hidden-information decision-making

### 建议讲稿
狼人杀很适合这个问题，因为它同时包含隐藏身份、公开发言、集体投票和对抗性操纵。好人不知道谁是狼，狼人知道更多信息，并且可以通过白天发言和夜晚击杀影响局势。这里的 `p_wolf` 可以理解为动态风险评分，suspicion score 是可疑度，herding 是群体压力。这个系统足够小，可以记录每一步；也足够复杂，可以研究误导、信任和声誉。

### 本页核心信息
狼人杀把风险评分、欺骗和集体决策压缩在一个可测量的小环境里。

### 转场
有了环境之后，研究问题本身也在不断变得更具体。

## Slide 3 — The question narrowed from game balance to information allocation

### 建议讲稿
项目最早问的是：哪些机制能降低狼人优势？后来问题变成：哪些信息路径在角色随机化之后仍然稳定？什么时候应该利用已有风险分数，什么时候应该探索更多目标？也就是说，研究从“开启某个机制会怎样”变成了“如何隔离并理解信息获取机制”。

### 本页核心信息
研究问题从胜率平衡转向了信息分配和机制隔离。

### 转场
为了做到这一点，每一章都按同一个实验循环推进。

## Slide 4 — Every chapter follows a hypothesis-to-revision loop

### 建议讲稿
整个项目遵循“假说、设计、模拟、记录、统计、修正假说”的循环。早期只看总体胜率就足够，因为是在验证机制有没有影响。后期研究搜索策略时，总胜率已经不够，所以加入 game-level logging，记录每一局第一验、查验路径、预言家生存和最终胜负。这样才能解释机制，而不是只报告排名。

### 本页核心信息
项目不是堆功能，而是用实验结果不断修正研究假说。

### 转场
这个循环依赖一个模块化的模拟器。

## Slide 5 — The simulator was built as separable experimental modules

### 建议讲稿
模拟器分成几个模块：核心状态负责玩家、阶段和胜负；行动模块包括预言家、女巫、猎人和狼人夜刀；社会信号模块包括 speech、`p_wolf`、herding 和 role prior；再往上是欺骗、可信度成本、speaker memory 和实验导出。这样的好处是可以单独开关机制，做 ablation 和对照实验。

### 本页核心信息
模块化设计让每个机制都能被单独检验。

### 转场
接下来先看最早的 baseline 为什么重要。

## Slide 6 — Low-information baselines established wolf dominance

### 建议讲稿
低信息 baseline 证明了游戏本身强烈偏向狼人。随机 baseline 里，好人胜率只有 7%；加入 suspicion voting 只有约 9%；加入 suspicion update 后到 15%。真正大的变化来自信息和干预：女巫行动后早期实验里好人胜率达到 49%。所以第一章的结论是：如果没有可靠信息，好人几乎无法抵抗狼人。

### 本页核心信息
低信息环境下狼人占优，信息机制是好人反击的基础。

### 转场
因此下一步自然是测试角色行动能提供多少信息和干预。

## Slide 7 — Information and intervention changed the game more than voting alone

### 建议讲稿
角色实验测试预言家、女巫和猎人的作用。预言家提供直接身份信息，好人胜率从 15% 提高到 23%。女巫通过救人和毒人改变生存路径，让好人胜率接近 49%。猎人有额外击杀能力，但也可能误杀，所以在这个早期设置里没有单调提升，只到约 46%。这说明角色能力有效，但会和误判风险产生交互。

### 本页核心信息
角色行动证明信息和干预很重要，但效果取决于具体互动环境。

### 转场
角色信息之后，项目进入更社会化的发言和信念更新。

## Slide 8 — Language-like signals turned play into social inference

### 建议讲稿
Stage 2 加入 Bag-of-Words 发言和 `p_wolf` belief update。发言不是真实自然语言，而是 accuse、defend、question、trust 这类可控信号。10-player 多 seed 结果显示，speech 可以把好人胜率提高到 65.16%；但加入 wolf deception 后，好人胜率会降到 21.60%。所以 speech 不是天然帮助好人，它是一条信息通道，也可以被狼人操纵。

### 本页核心信息
发言让游戏变成社会推理模型，但也打开了欺骗通道。

### 转场
如果预言家和发言都重要，狼人首先会攻击信息源。

## Slide 9 — Targeting the seer exposed the main village information channel

### 建议讲稿
wolf night strategy 诊断显示，`seer_first` 是早期最有利于狼人的夜刀策略，狼胜率约 39%。这不证明它是最优策略，但说明预言家是好人阵营的重要信息瓶颈。这个发现后来直接推动了 seer search 研究：如果预言家信息重要，那么预言家查验顺序也应该重要。

### 本页核心信息
预言家被识别为关键的信息源。

### 转场
但狼人不只在夜晚行动，也可以白天操纵发言。

## Slide 10 — Speech could help the village, so wolves learned to weaponize it

### 建议讲稿
Stage 3 测试狼人白天欺骗。不同欺骗方式差别很大：没有成本时，`false_accuse` 的狼人胜率达到 78%，`deflect_suspicion` 约 60%；但 `false_role_claim` 只有 23%，反而伤害狼人。这个结果说明欺骗不是一个统一变量，不同欺骗类型有不同收益和风险。

### 本页核心信息
欺骗能显著改变胜率，但具体策略选择非常关键。

### 转场
如果 false accusation 没有代价，模型会不真实，所以要加入可信度成本。

## Slide 11 — Deception only became plausible after costs were introduced

### 建议讲稿
credibility cost 的作用是让欺骗有风险。重复指控、错误指控和反复自我辩护都会提高说话者自己的 suspicion 和 `p_wolf`。加入成本后，`false_accuse` 从 78% 狼胜率降到约 50%，`deflect_suspicion` 和 adaptive 也降到约 46%。这使欺骗从“免费武器”变成了需要权衡的策略。

### 本页核心信息
可信度成本让欺骗机制更接近真实社会推理。

### 转场
下一步是把可信度从全局惩罚变成每个玩家对 speaker 的记忆。

## Slide 12 — Credibility became reputation, not just global suspicion

### 建议讲稿
Stage 4 加入 speaker-specific memory。每个玩家会记录其他发言者的 trust score。正确指控增加信任，错误指控降低信任，投票结果也会反过来更新 speaker trust。敏感性实验里，`trust_vote_weight` 从 0 到 0.40 时，狼人胜率从 47.80% 降到 36.40%。这说明记忆不是装饰，它可以实际改变投票和胜率。

### 本页核心信息
speaker memory 把可信度转化为个体化声誉。

### 转场
这些机制随后被放到更大的 10-player 环境里测试。

## Slide 13 — The larger setting preserved the main pattern but added noise

### 建议讲稿
10-player 设置包括 3 狼、4 村民、预言家、女巫和猎人。多 seed 结果显示，baseline 好人胜率是 43.68%；speech 到 65.16%；deception 让好人跌到 21.60%；credibility cost 回到 41.68%；speaker memory 到 60.32%。不过 trust-weighted herding 只有 48.56%，说明大局面里群体压力更容易放大错误，需要重新校准。

### 本页核心信息
10-player stress test 说明机制仍然有效，但更大系统更容易产生噪声和参数问题。

### 转场
除了机制本身，agent 的风险偏好也可能改变集体行为。

## Slide 14 — Risk appetite changed collective resilience

### 建议讲稿
risk preference 把玩家分成 conservative、neutral 和 aggressive。保守型更少做高风险指控，激进型更容易强行动。在 trust-memory 设置里，conservative-majority 的好人胜率是 61.44%，aggressive-majority 只有 49.04%。这说明群体风险偏好会改变系统韧性：过度激进可能增加误判，也更容易被狼人利用。

### 本页核心信息
风险偏好让 agent 异质化，并影响胜率和 payoff。

### 转场
到这里，项目转向一个狼人杀里常见但需要验证的说法：位置理论。

## Slide 15 — Position Theory Became a Research Chapter

### 建议讲稿
位置理论来自狼人杀经验，比如“边位可能更容易出狼”或者“预言家应该先验边”。在这里我们不把它当事实，而是当成可检验假说。初始设计比较 edge、inner、random、behavioral 和 side-based checking。但很快发现，如果角色总在固定座位，位置和身份会混在一起，策略效果可能只是固定分布造成的。

### 本页核心信息
位置学被转化成可验证的实验假说，而不是直接接受为经验规则。

### 转场
先看固定角色位置下的早期结果。

## Slide 16 — The early position results were suggestive but confounded

### 建议讲稿
固定角色位置实验里，`highest_p_wolf` 和 `random` 表现很强，`edge_first` 比 default 好，但没有统治其他策略。多 seed 中，`highest_p_wolf` 好人胜率约 67.40%，`random` 约 66.04%，`edge_first` 约 62.80%。问题是角色没有随机换座，所以 seat 和 role 纠缠在一起，不能说明 edge 本身有信息。

### 本页核心信息
固定座位结果有启发，但存在角色位置混淆。

### 转场
因此下一步必须随机化角色和座位的对应。

## Slide 17 — Edge seats were not intrinsically wolf-heavy

### 建议讲稿
随机座位角色实验保持 10-player 角色池不变，每局随机分配身份。理论上 3 狼 10 座，所以任意座位出狼概率应为 30%。结果 edge seats 是 30.23%，inner seats 是 29.85%，几乎等于理论期望。这削弱了强版本 edge theory：边位并不是天然更容易出狼。

### 本页核心信息
随机化后 edge 和 inner 狼概率都接近 30%，边位本身不是身份证据。

### 转场
接下来要看 edge-first 作为查验策略是否仍有独立优势。

## Slide 18 — Edge-first was not decisively better than random or inner-first

### 建议讲稿
形式化分析更谨慎。调整 first-check success、wolves-on-edge、seer seat、seer side 和 seed 后，`edge_first` 对 `random` 的 OR 是 1.05，p = 0.417；对 `inner_first` 的狼胜率差只有 0.24 percentage point。经过 Holm 多重比较校正后，相关比较没有显著。Holm correction 的作用是防止多次比较中误把随机波动当显著结果。

### 本页核心信息
edge-first 没有被证明优于 random 或 inner-first；位置只能作为弱 heuristic。

### 转场
那真正影响胜率的机制是什么？这需要 game-level logging。

## Slide 19 — Aggregate win rates were not enough to explain the mechanism

### 建议讲稿
game-level logging 记录每一局的第一验、查验路径、预言家生存和最终胜负。结果显示，第一验找到狼时，好人胜率约 47.59%；没有找到狼时约 34.17%。调整后的 odds ratio 是 1.76，95% CI 是 1.65 到 1.88，p < 0.001。odds ratio 表示胜利 odds 的相对变化。但这里要谨慎：这是强预测关联，不是严格因果证明。

### 本页核心信息
早期找到狼比座位类别更能预测好人胜利。

### 转场
这推动了一个新的假说：重点不是边位，而是搜索效率。

## Slide 20 — The mechanism shifted from seat category to information acquisition speed

### 建议讲稿
这页概括研究转向。最初假设 edge seats 有结构风险；随机化后发现 edge 不更狼；game-level logging 又发现 early discovery 很关键。所以新的假说是：预言家的 search path 是否能更快获得高价值信息，可能比检查哪类座位更重要。

### 本页核心信息
研究从位置类别转向信息获取速度和搜索路径。

### 转场
为了检验这个新假说，下一章比较 structured search。

## Slide 21 — Structured Sequential Search Tested the New Hypothesis

### 建议讲稿
structured search 关注的是预言家如何连续选择查验目标。这个问题更一般：当查验次数有限时，是应该追着当前风险最高的人查，还是保持覆盖和多样性？这也对应风险管理里的审计问题：资源有限时，如何安排信息获取顺序。

### 本页核心信息
structured search 把研究推进到顺序信息获取。

### 转场
下面看实验设计。

## Slide 22 — Four strategy families were compared across 35,000 games

### 建议讲稿
这个实验包括 14 个策略，5 个 seed，每个 strategy-seed 组合 500 局，总共 35,000 局，并启用 repeat guard 避免重复查验。策略分成 baseline、position、behavioral exploitation、structured diversification 和 hybrid proxy。这里 exploitation 指利用当前最高 `p_wolf` 或 suspicion；diversification 指用结构化路径扩大查验覆盖。

### 本页核心信息
实验把随机、位置、行为利用和多样化搜索放在同一框架中比较。

### 转场
描述统计首先显示多样化策略更有潜力。

## Slide 23 — The descriptive ranking favored diversified paths

### 建议讲稿
描述结果里，`alternate_sides` 好人胜率最高，约 44.16%；`right_to_left` 是 43.88%；`farthest_first` 是 42.88%；`random` 是 40.52%。相反，`highest_p_wolf` 是 34.88%，`highest_suspicion` 是 34.84%。这说明当前模型里，过早相信 noisy risk score 可能会缩窄搜索范围。

### 本页核心信息
描述统计上，多样化搜索优于追逐最高风险分数。

### 转场
但描述排名不能直接当成统计证明。

## Slide 24 — The ranking was promising, but the strongest supported result was negative

### 建议讲稿
正式统计结果更谨慎。整体 strategy effect 显著，LR = 118.69，p = 3.649e-19，说明策略总体确实有差异。但 `alternate_sides` 对 `random` 的 Holm p = 0.055，没有通过校正；`right_to_left` 对 `random` 也没有通过。最强的统计支持反而是负向的：`highest_p_wolf` 和 `highest_suspicion` 显著差于 random，Holm p 约 0.000276。

### 本页核心信息
positive structured-search 结果是 suggestive；最稳的发现是 behavioral exploitation 更差。

### 转场
这引出 exploration 和 exploitation 的解释。

## Slide 25 — Overusing risk scores narrowed search without improving information quality

### 建议讲稿
策略家族比较显示，structured diversification 的好人胜率约 42.66%，behavioral exploitation 只有 35.52%。而且 exploitation 没有明显提高 first-check discovery，还降低了预言家生存率。理论上，这说明当前风险分数早期噪声很大，预言家如果过度利用它，可能牺牲了探索覆盖。

### 本页核心信息
当前证据支持“不要过早 exploitation；需要保留搜索多样性”。

### 转场
不过 structured search 里出现了一个意外方向差异。

## Slide 26 — A directional gap became a validity problem, not a conclusion

### 建议讲稿
`right_to_left` 描述性上比 `left_to_right` 更强，约 43.88% 对 40.84%。但这不是原始假说，而且可能来自 seat number、player order 或 tie-break。所以我们不能说“从右往左查更好”。更正确的处理是把它当成 validity problem，先检查模拟器有没有方向或编号依赖。

### 本页核心信息
方向性优势目前是有效性问题，不是行为结论。

### 转场
因此我们做了 seat-order code audit。

## Slide 27 — Several mechanisms can depend on displayed numeric labels

### 建议讲稿
代码审计发现多个潜在依赖：行动顺序继承 player list；一些 tie-break 偏向低编号；1 到 5 被定义为 left，6 到 10 为 right；stable sorting 会保留原始顺序；speech RNG 还使用 `player_id`。这些不说明旧结果全部无效，但说明在解释方向策略之前，必须先中和 seat-label 和 order dependencies。

### 本页核心信息
模拟器中存在可能影响方向结果的编号和顺序依赖。

### 转场
下一步是用 mirror validation 做初步检验。

## Slide 28 — Mirroring labels did not create a clean counterfactual reversal

### 建议讲稿
mirror validation 保留 physical seat 和 underlying role assignment，但把显示编号镜像：1 对 10，2 对 9，依此类推。实验共 30,000 局。结果是 `right_to_left` 的优势没有简单反转：normal 下 left_to_right 42.48%，right_to_left 43.32%；mirrored 下 left_to_right 42.28%，right_to_left 43.72%。paired outcome agreement 只有约 46% 到 53%，说明镜像改变了后续轨迹，不是完全干净的反事实。

### 本页核心信息
mirror validation 暴露了复杂的 seat-order artifact，但没有完全解决它。

### 转场
因此现在必须把结论分层，而不是过度解释。

## Slide 29 — The project now separates supported conclusions from unresolved claims

### 建议讲稿
目前比较稳的结论是：信息流强烈影响胜率；edge seats 随机化后并不天然更狼；early wolf discovery 强烈预测好人胜利；seat-label/order dependencies 存在。比较有潜力的是 structured search、diversification、alternate_sides 和 right_to_left。不能声称的是 right-to-left 天然更优、某个方向有真实结构优势，或者 structured search 已被证明优于 random。

### 本页核心信息
当前研究已经清楚区分 supported、promising 和 not valid yet。

### 转场
最后看下一阶段如何解决未完成的问题。

## Slide 30 — Build a seat-order-neutral engine and isolate search mechanisms

### 建议讲稿
下一步不是继续加机制，而是建立 seat-order-neutral engine。要去掉 lower-ID deterministic advantages，避免 speech RNG 依赖显示编号，控制 player iteration order，并把方向从 numeric label 中解耦。之后再重新比较 left_to_right、right_to_left、alternate_sides 和 random。更大的研究问题是：在隐藏信息和有限行动次数下，bounded-information agent 应该怎样分配顺序查验？

### 本页核心信息
下一阶段要先解决实验有效性，再重新检验搜索机制。

### 转场
以上是完整汇报。下面是一分钟总结。

# 一分钟总结版

这个项目用狼人杀作为隐藏信息和社会推理的模拟环境。最早的 low-information baseline 显示狼人优势极大，好人胜率只有约 7%。加入角色信息、发言、`p_wolf`、herding、可信度成本和 speaker memory 后，好人胜率明显变化，说明信息流是核心机制。后来项目测试位置理论，发现随机化角色座位后 edge wolf probability 是 30.23%，inner 是 29.85%，基本等于理论期望 30%，所以强版本 edge theory 不成立。game-level logging 进一步发现，第一验找到狼时好人胜率约 47.59%，否则约 34.17%，说明早期信息发现更关键。structured search 里 alternate_sides 和 right_to_left 描述性表现最好，但没有通过 Holm 校正；highest_p_wolf 和 highest_suspicion 反而显著差于 random。最新 mirror validation 说明模拟器还有 seat-order dependencies，所以下一步是构建 seat-order-neutral engine，再干净地检验顺序搜索策略。

# 可能被老师问到的问题

## 1. 为什么选择狼人杀作为研究环境？

因为狼人杀同时包含隐藏身份、公开发言、投票、欺骗和声誉，而且每一步都可以记录。它是一个小规模但机制完整的社会推理实验环境。

## 2. 这是游戏模拟还是多智能体研究？

是以游戏为载体的多智能体模拟研究。游戏规则只是实验环境，真正研究的是 agent 在隐藏信息和对抗信号下如何更新信念并做集体决策。

## 3. 为什么位置学失败仍然有价值？

因为负结果也是研究结果。我们把 edge-seat 经验说法转化成可测试假说，并用随机化验证它。结论削弱了强版本位置学，也推动问题转向信息搜索效率。

## 4. 为什么第一验找到狼人和胜率有关？

第一验找到狼会很早改变好人的信息环境，影响后续 suspicion、`p_wolf`、发言解释和投票。数据上，好人胜率从约 34.17% 提高到 47.59%。

## 5. 为什么不能说这是因果关系？

因为 first-check success 不是独立随机分配的，它和策略、局势、预言家生存等因素相关。目前只能说是强预测关联，不能直接说它严格导致胜利。

## 6. 为什么 structured search 没有显著优于 random？

它描述性更好，但在多重比较校正后没有达到统计证据标准。尤其 `alternate_sides` 对 random 的 Holm p 是 0.055，所以只能说有潜力，不能说已证明更优。

## 7. 为什么 highest_p_wolf 反而更差？

可能是因为早期风险分数噪声很大。预言家过早追最高风险目标，会缩窄搜索范围，并可能降低生存率，所以 exploitation 反而不如 diversified search。

## 8. right_to_left 的优势是真的还是假的？

现在不能判断。它描述性更强，但没有通过校正，而且代码审计发现 seat order 和编号依赖。它目前是 validity issue，不是可靠行为结论。

## 9. 当前模拟器最大的 validity limitation 是什么？

主要是 player list 顺序、低编号 tie-break、数字化 left/right 定义、stable sorting 和 speech RNG 对 `player_id` 的依赖。这些都可能影响方向策略。

## 10. 下一步实验如何解决？

下一步会构建 seat-order-neutral engine，去掉低编号优势，解耦显示编号和随机机制，控制行动顺序，并用更干净的 paired random streams 重新测试主要搜索策略。
