"""Simula o failover do pool de chaves SEM gastar quota nem rede.

Prova que: (1) usa a chave 1; (2) ao estourar (429), castiga e troca pra 2;
(3) se a 2 também estoura, volta pra 1 quando o cooldown dela expira.
"""
import time

from gemini import PoolChaves


def cenario():
    pool = PoolChaves(["CHAVE_A", "CHAVE_B"])

    i, k = pool.proxima_disponivel()
    print(f"1) chamada inicial -> chave #{i + 1} ({k})")
    assert i == 0

    print("   chave #1 estoura o limite (429), castigo de 2s")
    pool.penalizar(0, 2)

    i, k = pool.proxima_disponivel()
    print(f"2) próxima chamada -> chave #{i + 1} ({k})  [failover!]")
    assert i == 1

    print("   chave #2 também estoura, castigo de 2s")
    pool.penalizar(1, 2)

    i, k = pool.proxima_disponivel()
    seg = pool.status()
    print(f"3) as duas em castigo -> escolhe a que libera primeiro: #{i + 1} "
          f"(cooldowns={seg}s)")

    print("   esperando o cooldown da chave #1 expirar...")
    time.sleep(2.1)
    i, k = pool.proxima_disponivel()
    print(f"4) após o reset -> volta pra chave #{i + 1} ({k})")
    assert i == 0

    print("\n✅ failover funcionando: as duas chaves se revezam certo.")


if __name__ == "__main__":
    cenario()
