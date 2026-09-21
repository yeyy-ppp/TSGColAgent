# 实验数据集清单

本项目已将实验数据集复制到项目内 `datasets/`，便于整体打包到另一台电脑运行。

| 数据集 | 当前项目内路径 | 来源路径 | 语言 | 数量/版本 |
| --- | --- | --- | --- | --- |
| TestEval | `datasets/TestEval` | `D:\2025_7_8\17\0707_agent_project\unittest-ai-agent\work\sourcesTestEval` | Python | 210 个 `.py` 文件 |
| HumanEval | `datasets/HumanEval` | `D:\2025_7_8\17\0707_agent_project\unittest-ai-agent\sources` | Python | 164 个 `.py` 文件 |
| HumanEvalJava | `datasets/HumanEvalJava` | 另一台电脑 `D:\wn\multi_evo_py\datasets\HumanEvalJava` | Java | 以另一台电脑实际文件数为准 |
| Defects4J Commons-Cli | `datasets/Defects4J/cli` | `D:\fx\jafx\chatunitest-core\src\main\java\cli` | Java | Commons-Cli 1.6.0 |
| Defects4J Commons-Csv | `datasets/Defects4J/csv` | `D:\fx\jafx\chatunitest-core\src\main\java\csv` | Java | Commons-Csv 1.10.0 |
| Defects4J Commons-Lang | `datasets/Defects4J/lang3` | `D:\fx\jafx\chatunitest-core\src\main\java\lang3` | Java | Commons-Lang 3.1.0 |
| Defects4J Gson | `datasets/Defects4J/gson` | `D:\fx\jafx\chatunitest-core\src\main\java\gson` | Java | Gson 2.10.1 |

说明：当前Java目录是对应项目版本的源码快照，不包含Defects4J缺陷编号、缺陷版/修复版切换脚本和完整开发者测试，因此可以进行JUnit、JaCoCo和PIT源码级测试生成实验，但不能直接据此计算真实缺陷揭示率BDR。正式Defects4J缺陷实验需要另行接入官方项目检出流程。

当前静态检查结果：TestEval 210个和HumanEval 164个Python文件全部通过AST解析；189个Java文件全部由Tree-sitter Java解析，识别144个类、30个接口、7个枚举和7个注解类型。`package-info.java`作为描述文件正确跳过测试目标选择。

运行依赖说明：HumanEval只使用Python标准库；TestEval的210个文件都会导入`sortedcontainers`，项目已在`pyproject.toml`、`uv.lock`和`依赖.txt`中统一声明`sortedcontainers>=2.4,<3.0`。

换机路径说明：默认优先使用项目自身`datasets`目录；也可以设置`TSG_DATASETS_ROOT=D:\wn\multi_evo_py\datasets`或传入`--datasets-root`。`HumanEvalJava`作为正式Java数据集自动发现并执行JUnit、JaCoCo和PIT。

批量执行说明：每个任务最终分为A、B、C、D、E五级，A/B/C为有效完整结果。R1处理全部任务；R2只恢复D/E，R2后仍为D/E则形成最终失败报告；R3统一优化全部C，包括R1原有的C和R2恢复得到的C，不存在R4。只有一个数据集目录内所有应处理源码都已有A/B/C结果，且源码文件清单、大小和修改时间签名没有变化，系统才依据`dataset_completion.json`整体跳过该目录。

知识保留说明：跨数据集经验以基础文件`knowledge_store/test_knowledge_guidance.json`和同名`.records/records-*.json`增量分片共同保存，可视化页面为`knowledge_store/test_knowledge_guidance_library.html`。迁移数据集和代码时必须同时保留基础文件及`.records`目录，不要把它们当作某次实验输出删除。
