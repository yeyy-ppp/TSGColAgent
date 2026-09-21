# LangGraph测试状态引导多智能体测试生成系统

> 2026-09-04验收更新：当前行为与已知边界以《功能验收报告_2026-09-04.md》及“记忆.md”顶部规则为准。对话优先模型+知识，模型不可用时知识自主回答，未知问题持久排队并在后台服务运行时自动补学；不是只在实验启用--llm时才允许对话。HumanEvalJava自动识别与显式java模式一致；本地163项不足164项参考规模，不冒充完整数据集。节点检查点有保存，但现有续跑主要为任务/轮次级。历史实验日志不改写。

本项目面向Python与Java源码生成高质量单元测试。LangGraph负责非线性编排、条件路由和SQLite检查点；项目自研的测试状态引导机制（TSG）通过共享TSG与测试状态中心承载缺口传播、测试意图、质量评估和停止条件。

## 架构

系统只有三个顶层智能体：

| 智能体 | 核心职责 | 禁止事项 |
| --- | --- | --- |
| 测试状态智能体 | 构建和修复共享TSG、质量评估、A-E分级、计算状态缺口、规划下一智能体及具体任务 | 不修改测试文件 |
| 测试生成智能体 | 生成候选、边界构造、执行工具链、结果验证、状态定位修复与状态目标优化 | 不负责最终质量分级和跨智能体调度 |
| 测试知识智能体 | 四维混合检索、成功/失败经验学习、与LLM共同对话、概念归纳和知识回写 | 不修改测试文件和质量指标 |

专项覆盖、断言、变异、边界、运行类型、有效性和Oracle修复模块属于测试生成智能体的内部能力，不是额外顶层智能体。

```text
测试状态智能体
  -> 测试知识智能体检索
  -> 测试生成智能体生成/修复、执行并验证结果
  -> 测试状态智能体依据验证证据评估质量、更新共享TSG并规划下一步
  -> 测试知识智能体学习
  -> 条件路由到状态自修复、继续生成、继续检索或结束
```

测试状态不完整或损坏时，测试状态智能体会重新分析源码、自修复共享TSG并再次规划，不是单向工作流。

## 质量门槛

正式高质量结果要求：

- 测试可收集、可编译且全部通过；
- 存在正常行为测试和有效断言；
- 不允许仅由`assertDoesNotThrow`、恒真断言或宽泛异常断言构成；
- 高质量行覆盖目标不低于0.90；
- 高质量分支覆盖目标不低于0.80；
- 高质量SFC目标不低于0.75；
- AE不低于0.75；
- 有效变异体不少于3个时，高质量Mutation不低于0.75；
- 高质量TSQ不低于0.82；
- PV为1，修复后的NRR为1。

最终结果统一分为A到E：A为高质量，B为整体良好且允许一个非关键指标偏低，C为可运行、有正常行为和有效断言但仍可优化，D为编译、导入、收集或执行无效，E为未运行、被中断或缺少必要证据。A/B/C均计入有效完整结果，D/E列入失败报告。每一轮出现D/E时都会立即写出当轮失败阶段、具体原因、原始证据、已采取措施和建议措施，并将失败模式保存到测试知识引导库；后续轮次会先检索这条经验，不需要等待整批实验结束。

正式实验固定最多三轮。R1运行全部任务并形成基线；测试生成智能体内部可围绕同一轮的可行性问题执行最多3次状态定位修复，这些内部修复不计为R2。R2只处理D/E，按失败类别检索原因和既有措施后重新生成并允许最多3次内部修复；R2后仍为D/E的任务直接形成最终失败报告。R3统一处理全部C，包括R1原本的C和R2恢复得到的C：保留现有通过测试，按最大质量缺口检索知识，使用状态目标优化提示最多尝试3次，达到A/B或没有增益时立即停止并保留历史最佳版本。系统不会开启R4。报告使用`B·R2`、`B·R3`和`D→C→B`展示等级、参与轮次、策略和轨迹。

为缩短真实实验时间，内部迭代采用分层评估。Python先串行执行最多8个由存活变异、未覆盖位置和状态缺口选出的高价值变异体，仅用于决定修复方向；准备形成正式结果时，最多选择20个变异体，并复用筛查结果。最终Mutation、TSQ、A-E等级和知识学习只采用正式评估。不可运行的D/E候选不会执行覆盖或变异；内部修复或优化达到可行目标、没有产生代码变化或没有质量增益时提前停止，因此“最多3次”不是固定执行3次。Java的JUnit与JaCoCo合并为一次构建，候选稳定后才执行PIT，并保留增量编译产物。HumanEvalJava类级任务默认使用2个互相隔离的工作槽；其他Java目录和项目仍保持原串行策略。源码、测试或依赖配置未变化时，系统按哈希复用覆盖、变异或Java工具链证据；任一输入变化会自动失效缓存。

Python数据集默认以4个任务并行处理，适合TestEval这类200余文件的独立任务集合；每个任务内部的pytest、coverage和Mutation仍串行，避免证据混写。本地Ollama模型最多同时处理2个请求，防止4个任务同时占满显存。HumanEvalJava默认2任务并行，每个类拥有独立源码、测试、构建和报告目录，只共享Maven依赖缓存，并在正式轮次结束后统一合并知识；可用`--humanevaljava-workers`设置1至4。Defects4J、普通Java目录和Java项目仍保持串行。

这里的4并行是“同一个Python数据集目录内最多4个源码任务同时推进”，不是同时运行4个数据集。四个任务只有在请求模型时才共享2个Ollama通道；没有占用模型通道的任务仍可继续执行源码分析、pytest、覆盖率或变异验证。数据集目录本身继续按顺序运行。

```text
TSQ = 0.30*SFC + 0.20*AE + 0.20*MS + 0.15*PV + 0.15*NRR
```

Mutation不适用时对其余有效指标重新归一化，不把缺失结果虚记为0分或满分。

## 双语言能力

Python使用AST、pytest、coverage.py、运行时观察和变异测试，支持函数、类方法、异步函数、生成器、循环、异常、模式匹配和动态类型输入。

Java使用Tree-sitter Java AST，失败时才使用兼容降级解析；能够识别类、接口、枚举、注解类型、记录、继承、泛型、重载、Override、分支、循环、返回和抛出，并通过JUnit 5、Maven/Gradle、JaCoCo和PIT产生真实证据。

## 安装

```powershell
python -m pip install -e .
```

主要依赖已写入`pyproject.toml`和`uv.lock`：pytest、coverage、sortedcontainers、LangGraph、SQLite checkpointer、Tree-sitter和Tree-sitter Java。TestEval的210个源码文件都会导入sortedcontainers，换机时不能省略该依赖。

安装后可执行：

```powershell
python -c "import sortedcontainers; print(sortedcontainers.__version__)"
```

## 实时实验台

新版前端完整源码和可直接运行的构建结果位于`frontend/`，不再依赖项目外的旧演示页面。执行`main.py`、`run_agent.py`、`batch_generate_tests.py`或`run_all_datasets.py`任一正式实验命令时，系统都会启动独立执行控制与展示服务并自动打开`http://127.0.0.1:8765`。默认进入“实验总览”，同时提供“正在运行”“已跑完”“排队中”和每个数据集的独立视图。一个批量命令只打开一次，后续数据集和任务在同一页面实时更新；页面关闭或服务异常不会中断实验。

页面展示Python/Java以及文件级、项目级和混合实验范围。实验总览以全部数据集矩阵、六维质量图、A-E结构、覆盖率×Mutation×AE散点图、变异分布和累计耗时图展示总体结果；切换到单个数据集后，全部图表、任务筛选和报告同步限定到该数据集。测试状态中心和测试生成过程以证据完整度、状态分布、失败分布、轮次流量、处理路径、最终等级和逐任务耗时图为主，文字明细默认折叠。报告和单元测试问答统一由测试知识智能体处理；支持多个独立持久化对话，对话名称不绑定当前任务，系统根据问题内容识别实验或任务上下文。使用`--llm`时，测试知识智能体沿用对应实验的模型配置共同回答；对话中形成的单元测试概念先归纳为“正在学习”，被后续真实任务采用并取得可行结果后累计验证，达到要求后标为“已掌握”，但仍持续接受新证据。未启用模型时仍可查询报告中的确定性数据。

实验范围菜单固定提供“实验总览”和各数据集入口，数据集列表可独立滚动。TestEval、HumanEval、HumanEvalJava和Defects4J分别显示自身语言及文件/函数/类/项目层级。旧实验若只保存了恢复会话的几秒钟，页面会由所有任务历史耗时按当时任务并发数恢复累计时长，并明确区分最近恢复时间和完整累计时长。只有测试文件、没有有效执行证据的数据集会标为“待重新验证”，不会用零值伪装真实覆盖率或变异结果。

除终端命令外，也可在页面“启动实验”中选择单文件/类、项目/目录或数据集根目录并启动，还可以为本次实验切换模型名称、服务地址和密钥。配置只提交到本机后端并进入原有LLM调用链，不保存在浏览器；该操作调用相同的`main.py`、`batch_generate_tests.py`或`run_all_datasets.py`，不会复制智能体逻辑。网页提交的目录实验进入串行队列：当前目录全部处理结束、对应进程退出后，下一目录才会启动；终端入口也会在结束时回写“已完成”或“失败”。

不需要页面时显式使用`--no-ui`。端口冲突时可以设置`TSG_UI_PORT`，彻底关闭自动页面也可以设置`TSG_UI_ENABLED=0`。前端开发命令为：

```powershell
cd frontend
npm install
npm run dev
```

## 单文件运行

```powershell
python -B main.py --source datasets\HumanEval\task_000.py --out runs\humaneval_000 --max-iterations 3
python -B main.py --source datasets\Defects4J\cli\Util.java --out runs\java_util --max-iterations 3
```

启用本地大模型：

```powershell
python -B main.py --source examples\sample_target.py --out runs\sample --llm --llm-model deepseek-r1:14b
```

兼容旧参数`--sfq`，推荐使用`--tsq`。

## 数据集运行

```powershell
cd D:\wn\multi_evo_py
$env:TSG_DATASETS_ROOT="D:\wn\multi_evo_py\datasets"
python -B run_all_datasets.py --datasets-root "D:\wn\multi_evo_py\datasets" --limit-per-dataset 1
python -B run_all_datasets.py --datasets-root "D:\wn\multi_evo_py\datasets" --llm
```

数据集根目录按“命令行参数、`TSG_DATASETS_ROOT`/`STATEFLOW_DATASETS_ROOT`、项目内`datasets`、`D:\wn\multi_evo_py\datasets`”的顺序解析。系统会运行TestEval、HumanEval、HumanEvalJava以及cli、csv、lang3、gson四组Java源码；其他顶层Python/Java目录也会自动识别。A/B/C计入有效完整结果，D/E进入后续轮次或最终失败报告。

HumanEvalJava按单源码隔离到独立Maven工作区，不能把整个163题目录复制到每个任务中。迁移包内的`datasets/HumanEvalJava`若缺失，可用`scripts/restore_humanevaljava_dataset.py`从保留的状态图恢复；当前分发目录已恢复163个源码并完成整体编译检查。

完整批量结束后会写入`dataset_completion.json`。再次运行时，只有目录内所有应处理任务都已得到A/B/C，系统才会在扫描源码前跳过整个数据集目录；只要缺少一个任务或存在D/E，就只续跑未解决任务。

在另一台正式实验电脑上，长期知识应放在代码目录之外。下面这条命令会在外部文件不存在时把项目内现有知识初始化到`D:\wn\evo\test_knowledge_guidance.json`，之后始终读取并追加该文件；如果文件已经存在，新代码包不会覆盖它。迁移旧实验知识时也可以预先把提炼后的`D:\wn\evo`目录打包到目标电脑：

```powershell
python -B run_all_datasets.py --datasets-root "D:\wn\multi_evo_py\datasets" --out-root "D:\wn\multi_evo_py\runs" --llm --knowledge-store "D:\wn\evo\test_knowledge_guidance.json"
```

续跑会直接读取每个任务的最新摘要和轮次进度。已经完成R1且具有明确失败原因或诊断证据的D/E任务不会再次执行R1，而会携带原始失败证据和知识检索结果进入R2；旧摘要若只有失败标签而没有原因、错误或措施，则重跑R1以补齐可信证据。每完成一个R2或R3任务，批量统计就立即刷新。后续轮次开始前会备份上一轮最佳测试，候选无增益、损坏或运行中断时自动恢复，避免续跑覆盖已有有效结果。

时间统计不会在续跑时清零。每个任务通过`task_runtime.json`保存各次真实运行区间，异常中断截止到最后任务产物时间，空闲/关机时间不计入；页面依次展示单任务累计耗时、数据集累计耗时和全实验累计总时长。旧摘要中的运行时间会在首次续跑时自动迁移。

Java第一次运行需要Maven Central网络访问，或者在打包时保留`java_workspace/.m2`依赖缓存。Maven可以通过项目wrapper、PATH、`MAVEN_CMD`、`MAVEN_HOME`或`M2_HOME`定位。

## 输出

每个任务目录包含生成测试、`stateflow_summary.json`、`state_flow_graph.json`、离线HTML/SVG报告和`.langgraph/checkpoints.sqlite`。批量目录还包含A-E统计、轮次轨迹、D/E失败报告和`dataset_completion.json`。这些文件名为兼容名称，内容由测试状态中心作为共享TSG数据读取。

跨实验知识独立保存在`knowledge_store/test_knowledge_guidance.json`，可视化入口为`knowledge_store/test_knowledge_guidance_library.html`，名称统一为“测试知识引导库”。删除某次`runs`结果不会丢失长期经验；打包迁移时应保留`knowledge_store`。

旧实验中的重复经验已经按语言、任务复杂度、失败类别和证据强度去重归纳后合并到该知识库。前端显示“支持次数”和“独立任务数”，区分同一任务的重复记录与跨任务验证；批量摘要本身不作为一条可学习知识展示。

完整共享TSG数据不放入LangGraph状态快照；检查点只保存文件引用、版本、测试意图、证据引用、指标、预算和路由状态，避免重复复制大对象。代码中的`state_model`字段和`test_state_model.py`文件名仅为向后兼容，不是前端或方法名称。

## 初始实验状态

分发包不附带已执行实验、任务报告或指标结果。启动单文件、目录或数据集实验后，实时实验台才会登记并展示对应的Python/Java任务、共享TSG、覆盖率、断言质量、变异结果和A-E等级。`examples/`只保留用于快速检查运行环境的源码样本，不包含生成结果。

## 自检

```powershell
python -B -m pytest -q
```

打包前已完成多文件发现、多目录串行队列、监控融合和前端详情检查；检查产生的实验目录和登记信息均已清理。

## 主要代码

- `orchestration/`：LangGraph状态、非线性路由、SQLite检查点；
- `monitoring/`：独立执行控制与实时展示服务，提供SSE、实验登记、网页启动、产物读取和知识问答接口；
- `frontend/`：实时实验台源码与构建结果；
- `agents/test_state_agent.py`：测试状态智能体；
- `agents/generation_agent.py`、`agents/execution_agent.py`：测试生成智能体及执行模块；
- `agents/test_knowledge_agent.py`：测试知识智能体；
- `graph/test_state_model.py`、`graph/structured_graph_builder.py`：共享TSG状态结构（文件名向后兼容）；
- `graph/adaptive_scheduler.py`：状态缺口与任务调度；
- `graph/experience_memory.py`：四维混合检索和长期经验；
- `analysis/`：Python/Java结构分析；
- `executor/`：pytest、JUnit、coverage、JaCoCo、PIT和运行时工具；
- `repair/`：状态定位修复策略；
- `visualization/`：共享TSG、源码证据和批量报告。
