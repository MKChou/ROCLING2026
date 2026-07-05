# ROCLING 2026 短论文

面向高龄语音互动应用之 ASR 部署方案比较：准确度、延迟与幻觉稳健性之权衡。

## 内容

| 文件 | 说明 |
|------|------|
| `rocling2026_draft.tex` | 论文初稿（实验数据待补） |
| `rocling2026.bib` | 参考文献 |
| `rocling2026.tex` / `rocling2026.sty` | ROCLING 2026 官方模板 |
| `ROCLING2026_研究規劃.md` | 研究计划 |
| `實驗交付手冊.md` | 实验步骤与数据交付格式 |
| `dict.xlsx` | 台语汉字↔国语对照词典（编 ACP 测试句用） |
| `reference/` | 医师提供之参考文献 PDF |

## 编译论文

使用 XeLaTeX 编译 `rocling2026_draft.tex`（建议 Overleaf，需标楷体字型）。

```bash
xelatex rocling2026_draft.tex
bibtex rocling2026_draft
xelatex rocling2026_draft.tex
xelatex rocling2026_draft.tex
```

## 会议

- [ROCLING 2026](https://rocling2026.github.io/NTHU_rocling_2026/)
- 投稿截止：2026/07/20
- EasyChair：https://easychair.org/conferences/?conf=rocling2026
