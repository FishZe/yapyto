# YaPyTo

`YaPyTo`是<del>下一代</del>信息学竞赛题目格式转换和配置文件生成工具，将符合[`hydro`](https://github.com/hydro-dev/Hydro)的数据和`config.yaml`的题目，或由[`hydro题库`](https://hydro.ac/d/tk/p)下载的题目，转换为符合[`sastoj`](https://github.com/NJUPT-SAST/sastoj/)[`schema`](https://github.com/Jisu-Woniu/rsjudge-test-cases-schema)的格式；同时也可以识别测试数据，生成满足条件的配置文件；给定数据生成器或标程运行的命令，也可以生成输入输出文件和对应的配置文件，来源于[`yarusto`](https://github.com/NJUPT-SAST/yarusto)。

## 兼容性

1. `sastoj`目前不支持`special-judge`和`interactive`类型的题目，因此，`hydro`格式的`config.yaml`中`type`和`checker_type`不都为`default`的题目暂时不受支持
2. `sastoj`目前不支持`subtask`的指定评分方式，仅支持取所属测试点中的最小值，`config.yaml`中包含`subtask`的，且`type`为`max`的不受支持，`min`将保持为`subtask`，`sum`将会被拆分为`cases`，且包含多个`subtask`时，多个`subtask`的`type`必须相同。
3. `sastoj`目前不支持针对`case`和`subtask`级别的`time_limit`和`memory_limit`，但`YaPyTo`仍在`case`和`subtask`中保留了这些字段，但出题时请注意修改整题的时间和内存限制
4. `YaPyTo`和`sastoj`所使用的测试点分数补全方法有所区别，体现在`YaPyTo`对于未指定分数的测试点分数补全将更加平均，同一份配置文件经过`YaPyTo`后可能分数有所区别。
5. 所有`subtask`的子任务依赖不被支持，会被忽略。

## 转换方式
1. 以一份后缀为`.out`或`.ans`的文件作为识别为题目数据的特征，包含`config.yaml`的题目数据文件将试图进行读取和转换，不包含或转换失败的，则会通过目录下的输入输出文件识别为测试点并补全分数。
2. 对于包含多个`subtask`的`config.yaml`，只有`type`相同，且为`min`或`sum`时，会被转换。
3. 无论多个或单个`subtask`，类型为`sum`的`subtask`会被拆分为多个`case`，并忽略该`subtask`的`id`、子任务依赖和时间空间限制；类型为`min`的`subtask`将会保留为`subtask`，但子任务依赖依旧会被忽略。（注意，即使保留了`subtask`的时间与空间限制，但`sastoj`目前仍不支持）
4. 对于未指定分数的`case`和`subtask`，会根据满分和已有分数计算分数，单个测试点的最小分数为`1`，默认整题分数为`100`，分数算法为剩余未分配的分数整除剩余未分配个数。类型为`sum`，未指定分数的`subtask`会在拆分为`case`后再计算分数，但已指定分数的测试点不受影响，已指定分数之间冲突时配置文件将转换失败。
5. 输入输出文件一致且时间与空间限制相同的测试点将被识别为相同的测试点，会被合并，分数为二者总和。
6. 配置文件转换失败或不存在配置文件时，会通过目录下的文件试图生成位置文件，当不包含后缀名的文件名相同的`.in`和`.out`/`.ans`文件会被识别为一对测试点。

## 用法

安装依赖
```bash
pip install -r requirements.txt
```
使用
```text
usage: main.py [-h] [-i INPUT] [-o OUTPUT] [--rename-output] [--generate] [-c CASE] [--generate-command GENERATE_COMMAND] [--std-command STD_COMMAND]

A converter that convert the config.yaml from hydro to the config.toml of sastoj schema.

options:
  -h, --help                            show this help message and exit
  -i INPUT, --input INPUT               input directory, such as ../testdata
  -o OUTPUT, --output OUTPUT            output directory
  --rename-output                       rename the output file to answer file
  --generate                            generate the input file or answer file
  -c CASE, --case CASE                  case sum
  --generate-command GENERATE_COMMAND   the command to generate the input file
  --std-command STD_COMMAND             the command to generate the answer file
```

1. 根据给定`hydro`题目文件转换，使用`-i`指定题目文件目录，使用`-o`指定输出目录

    ```bash
    python main.py -i ./example/problem -o ./example/testdata
    ```

2. 给定不包含配置文件的测试点输入输出文件，生成配置文件，并补全分数，命令同上

3. 给定测试输入文件和标程运行命令，生成配置文件和标准输出：

    ```bash
    python main.py --generate -i ./example/problem_input --std-command './std' -o ./example/testdata
    ```

4. 给定数据生成器运行命令和标程运行命令，生成配置文件和测试点输入输出文件，使用`-c`指定生成数量，默认为`10`:

    ```bash
    python .\main.py --generate -c 22 --generate-command "python -c 'import random;print(random.randint(0, 65536), random.randint(0, 65536))'" --std-command "python -c 's = input().split();print(int(s[0]) + int(s[1]))'"
    ```

### 输入目录应满足的格式：
1. `type=custom`

    如果使用目录下的输入文件，给定标程运行命令，生成标准输出，请使用如下目录结构（不包含输出文件和配置文件）

    ```text
    .
    ├── 1.in
    ├── 1.out
    ├── 2.in
    ├── 2.out
    ...
    ├── 9.in
    ├── 9.out
    ├── 10.in
    ├── 10.out
    └── config.yaml

    1 directory, 21 files
    ```
2. `type=hydro`
   ```text
    .
    ├── 1
    │   ├── problem.md
    │   ├── problem.yaml
    │   └── testdata
    │       ├── 1.in
    │       ├── 1.out
    │       └── config.yaml
    ├── 45
    │   ├── problem.md
    │   ├── problem.yaml
    │   └── testdata
    │       ├── 1.in
    │       ├── 1.out
    │       └── config.yaml
    └── 导入指南.txt

    5 directories, 11 files
   ```
