# Complete Collatz Conjecture / コラッツ予想の完全拡張

Python tools for exploring and extending the **Complete Collatz Conjecture** —  
a full extension of the classical Collatz dynamics to all integers using the Odd-Zero Paradigm.

**コラッツ予想の完全拡張** の計算と出力を行う Python ツール集です。  
**Odd-Zero Paradigm** を用いて、全ての整数に対するコラッツ動力学を拡張します。

---

## 📖 About the Conjecture / 予想について

The **Complete Collatz mapping** extends the classical **Collatz Conjecture** to all integers via the **Odd-Zero Paradigm**,  
which treats zero as an odd number and allows for the dynamics to unify both positive and negative integers.

**コラッツ予想の完全拡張**は、**Odd-Zero Paradigm**を通じて、  
非ゼロ整数に対してコラッツ動力学を拡張するものです。0を奇数として扱い、正負の整数を一貫して扱えるようにします。

The extended mapping is defined as:

\[
T(n) =
\begin{cases}
n / (-2), & \text{if } n \text{ is even} \\
3n - 1, & \text{if } n \text{ is odd}
\end{cases}
\]

---

## 🗂 Scripts / スクリプト一覧

| Script name | Description (English) | 説明 (日本語) |
|-------------|------------------------|--------------|
| [`collatz_o_operator.py`](collatz_o_operator.py) | Full range scan, ABS1/NON-ABS1 classification, and cycle detection for the extended Collatz dynamics | コラッツ動力学の全範囲走査、ABS1/NON-ABS1分類、サイクル検出 |


---

## 🚀 Features / 機能

- **Full-range scan / 全範囲走査**: 任意の開始値・終了値を指定（0は自動で除外）
- **Cycle classification / サイクル分類**: 各初期値について、収束するかどうかを分類
- **ABS1 / NON-ABS1 classification**: ABS1（絶対値1のループ）とNON-ABS1（その他のループ）の分類
- **Multi-core processing / マルチコア処理**: 並列計算を利用した高速化
- **Progress display / 進捗表示**: 大規模実行時の進捗表示

---

## 📦 Requirements / 必要環境

- Python 3.8+
- No external dependencies（標準ライブラリのみ使用）

---

## ⚙️ Usage / 使い方

1. **Clone the repository / リポジトリをクローン**
```bash
git clone https://github.com/LumaVoice/CompleteCollatzConjecture.git
cd CompleteCollatzConjecture
```

2. **Edit settings at the top of the script / スクリプト冒頭の設定を編集**
Example from collatz_o_operator.py:
```python
START: int = -1000
END: int = 1000
STEP_LIMIT: int = 1000
OUT_CSV: str = "complete_collatz_output.csv"
WRITE_SUMMARY_CSV: bool = True
LOG_NONCONVERGED: bool = True
PROGRESS_EVERY: int = 5000
```

3. **Run the script / スクリプトを実行**
```bash
python3 collatz_o_operator.py
```
## 📜 License / ライセンス

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

このプロジェクトは MITライセンス で公開されています。詳細は [LICENSE](LICENSE) をご覧ください。

---

## ✍️ Author / 作者

- **Ryosuke Miyazawa**  
- Proposer of the Shadow Collatz Conjecture / シャドウ・コラッツ予想提唱者  
- Contact / 連絡先: luma.voice@proton.me

---

## 🔗 External Links / 外部リンク

- **arXiv author page**: [https://arxiv.org/a/lumavoice.html](https://arxiv.org/a/lumavoice.html)
- **Zenodo record**: [https://zenodo.org/records/16754305](https://zenodo.org/records/16754305)
- **OEIS profile**: [https://oeis.org/wiki/User:Ryosuke_Miyazawa](https://oeis.org/wiki/User:Ryosuke_Miyazawa)


