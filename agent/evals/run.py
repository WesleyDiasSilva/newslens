"""Roda os evals determinísticos sobre um dataset de briefings gravados.

Uso:
    python evals/run.py                          # dataset.json (deve passar)
    python evals/run.py evals/dataset_ruim.json  # caso com regressão (deve quebrar)
"""
import json, sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from checks import CHECKS

def main():
    base = os.path.dirname(os.path.abspath(__file__))
    caminho = sys.argv[1] if len(sys.argv) > 1 else os.path.join(base, "dataset.json")
    with open(caminho, encoding="utf-8") as f:
        dataset = json.load(f)

    print(f"\n  Eval set: {caminho}  ({len(dataset)} casos)\n")
    total_falhas = 0
    for item in dataset:
        falhas = []
        for nome, fn in CHECKS:
            ok, motivo = fn(item)
            if not ok:
                falhas.append(f"{nome} ({motivo})")
        marca = "\033[92m✔\033[0m" if not falhas else "\033[91m✗\033[0m"
        status = "PASS" if not falhas else "FAIL"
        print(f"  {marca}  [{status}]  {item['tema']}")
        for f_ in falhas:
            print(f"          └─ {f_}")
        total_falhas += len(falhas)

    print()
    if total_falhas == 0:
        print("  \033[92mTodos os checks passaram.\033[0m\n"); sys.exit(0)
    print(f"  \033[91m{total_falhas} check(s) falharam — regressão detectada.\033[0m\n"); sys.exit(1)

if __name__ == "__main__":
    main()
