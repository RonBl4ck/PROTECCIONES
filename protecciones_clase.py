import numpy as np
import matplotlib.pyplot as plt

# =====================================================================
# 1. ENTRADA DE PARAMETROS (CON VALORES POR DEFECTO DE CLASE)
# =====================================================================
print("=" * 70)
print(" CONFIGURACION DEL SISTEMA - ERCMF MULTIETAPA | LNavarrete")
print("=" * 70)

try:
    netapas = input("Ingrese el numero de etapas (defecto 3): ")
    netapas = int(netapas) if netapas.strip() else 3
except ValueError:
    netapas = 3

try:
    f0 = input("Frecuencia inicial [I] (Hz, defecto 60.00): ")
    f0 = float(f0) if f0.strip() else 60.00
except ValueError:
    f0 = 60.00

try:
    H = input("Constante de inercia [H] (seg, defecto 3.00): ")
    H = float(H) if H.strip() else 3.00
except ValueError:
    H = 3.00

try:
    f_min_perm = input("Frecuencia minima permisible (Hz, defecto 56.00): ")
    f_min_perm = float(f_min_perm) if f_min_perm.strip() else 56.00
except ValueError:
    f_min_perm = 56.00

try:
    f_ajuste_1 = input("Ajuste de la primera etapa (Hz, defecto 59.00): ")
    f_ajuste_1 = float(f_ajuste_1) if f_ajuste_1.strip() else 59.00
except ValueError:
    f_ajuste_1 = 59.00

try:
    t_rele = input("Tiempo del rele de minima frecuencia (seg, defecto 0.30): ")
    t_rele = float(t_rele) if t_rele.strip() else 0.30
except ValueError:
    t_rele = 0.30

try:
    t_int = input("Tiempo del interruptor (seg, defecto 0.10): ")
    t_int = float(t_int) if t_int.strip() else 0.10
except ValueError:
    t_int = 0.10

T_total = t_rele + t_int

try:
    f_intervalo = input("Intervalo de frecuencia de seguridad (Hz, defecto 0.10): ")
    f_intervalo = float(f_intervalo) if f_intervalo.strip() else 0.10
except ValueError:
    f_intervalo = 0.10

# Alivios por etapa
alivios = {}
print(f"\nIngrese los porcentajes de alivio para cada una de las {netapas} etapas:")
for i in range(1, netapas + 1):
    def_val = 10 if i == 1 else 20
    try:
        val = input(f"  Alivio Etapa {i} (%, defecto {def_val}%): ")
        val = float(val) if val.strip() else def_val
    except ValueError:
        val = def_val
    alivios[i] = val / 100.0

# =====================================================================
# 2. ALGORITMO GENERAL DINAMICO (PUNTO MAS CERCANO A LA IZQUIERDA)
# =====================================================================
def calcular_puntos_de_etapa(num_etapas_limite, deficit_inicial, f_ajustes):
    """
    Calcula dinamicamente los puntos R y D de cada etapa.
    Busca siempre el punto mas cercano a la izquierda de entre los ya calculados.
    """
    puntos = [
      { "id": "O", "t": 0.0, "f": f0, "p": deficit_inicial, "desc": "Punto Inicial O" }
    ]

    for i in range(1, num_etapas_limite + 1):
        # 1. Calcular Ri (Activacion)
        f_ajuste_i = f_ajustes[i]
        
        # Buscar el punto mas cercano a la izquierda en frecuencia (menor diferencia f >= f_ajuste_i)
        left_r = None
        min_f_diff = float('inf')
        for pt in puntos:
            if pt["f"] >= f_ajuste_i:
                diff = pt["f"] - f_ajuste_i
                if diff < min_f_diff:
                    min_f_diff = diff
                    left_r = pt
                    
        df_dt_r = (f0 * left_r["p"]) / (2 * H)
        t_ri = left_r["t"] + (f_ajuste_i - left_r["f"]) / df_dt_r
        
        puntos.append({
            "id": f"R{i}",
            "t": t_ri,
            "f": f_ajuste_i,
            "p": left_r["p"],
            "desc": f"R{i} (Activacion Etapa {i})",
            "orig_id": left_r["id"],
            "p_deficit_name": left_r["p"]
        })

        # 2. Calcular Di (Deslastre)
        t_di = t_ri + T_total
        
        # Buscar el punto mas cercano a la izquierda en tiempo (maximo t <= t_di)
        left_d = None
        max_t = -float('inf')
        for pt in puntos:
            if pt["t"] <= t_di:
                if pt["t"] > max_t:
                    max_t = pt["t"]
                    left_d = pt
                    
        df_dt_d = (f0 * left_d["p"]) / (2 * H)
        f_di = left_d["f"] + df_dt_d * (t_di - left_d["t"])
        p_after_di = left_d["p"] + alivios[i]
        
        puntos.append({
            "id": f"D{i}",
            "t": t_di,
            "f": f_di,
            "p": p_after_di,
            "desc": f"D{i} (Deslastre Etapa {i})",
            "orig_id": left_d["id"],
            "p_deficit_name": left_d["p"]
        })
        
    return puntos

# =====================================================================
# 3. EJECUCION DE LOS CALCULOS SECUENCIALES
# =====================================================================

f_ajustes = { 1: f_ajuste_1 }
resultados_etapas = {}
alivio_acumulado = 0.0

for k in range(1, netapas + 1):
    alivio_acumulado += alivios[k]
    deficit_k = -alivio_acumulado
    
    # Calcular trayectoria para escenario k
    puntos_k = calcular_puntos_de_etapa(k, deficit_k, f_ajustes)
    resultados_etapas[k] = puntos_k
    
    # Obtener f(D_k)
    f_dk = next(p["f"] for p in puntos_k if p["id"] == f"D{k}")
    
    if k < netapas:
        f_ajustes[k + 1] = round(f_dk - f_intervalo, 3)

f_nadir = next(p["f"] for p in resultados_etapas[netapas] if p["id"] == f"D{netapas}")
f_min_check = round(f_nadir - f_intervalo, 3)
es_valido = f_min_check >= f_min_perm

# =====================================================================
# 4. IMPRESION DE PASOS EN EL FORMATO DE CLASE
# =====================================================================

print("\n" + "=" * 70)
print(" REPORTE PASO A PASO EN EL FORMATO DE CLASE")
print("=" * 70 + "\n")

def imprimir_reporte_etapa(puntos_list, tab_index):
    # Generar orden de puntos
    order = []
    for i in range(1, tab_index + 1):
        order.append(f"R{i}")
        order.append(f"D{i}")
        
    puntos_calculados = []
    for ident in order:
        pt = next((p for p in puntos_list if p["id"] == ident), None)
        if pt:
            puntos_calculados.append(pt)
            
    for pt in puntos_calculados:
        left_pt = next(p for p in puntos_list if p["id"] == pt["orig_id"])
        p_val = pt["p_deficit_name"]
        
        p_comment = ""
        if tab_index == 1:
            p_comment = f"(por el {int(alivios[1]*100)}%)" + (" (seguimos en primera etapa)" if pt["id"].startswith("D") else "")
        else:
            if pt["id"].startswith("R"):
                if pt["id"] == "R1":
                    total_alivio = sum(alivios[s] for s in range(1, tab_index + 1))
                    p_comment = f"(por el peor escenario de deficit, {int(total_alivio*100)}%)"
                else:
                    p_comment = "(por ubicacion sigue en esta etapa, aun no opera el deslastre de la etapa anterior)"
            else:
                if pt["id"] == f"D{tab_index}":
                    p_comment = "(YA SE RECHAZO LA ETAPA ANTERIOR, QUITAMOS EL ALIVIO Y ESTE SERA EL NADIR)"
                else:
                    p_comment = "(YA SE RECHAZO LA ETAPA ANTERIOR, QUITAMOS EL ALIVIO EN ESTE TRAMO)"

        print(f"{pt['orig_id']} a {pt['id']}:")
        print(f"  I = {f0:.3f}Hz")
        print(f"  H = {H:.3f}")
        print(f"  P = {p_val:.1f} {p_comment}")
        print(f"  F = {left_pt['f']:.3f}Hz (frecuencia inicial {pt['orig_id']})")
        
        if pt["id"].startswith("R"):
            print(f"  G = {pt['f']:.3f}Hz (la frecuencia en {pt['id']})")
            print(f"  T = {left_pt['t']:.3f}seg (tiempo de {pt['orig_id']})")
            print(f"  U = {pt['t']:.3f}seg (tiempo a descubrir)")
        else:
            print(f"  G = {pt['f']:.3f}Hz (la frecuencia en {pt['id']})")
            print(f"  T = {left_pt['t']:.3f}seg (tiempo de {pt['orig_id']})")
            print(f"  U = {pt['t']:.3f}seg (tiempo de {pt['id']})")
        print()

for k in range(1, netapas + 1):
    if k == netapas:
        print(f"COMPROBACION DE LA MINIMA FRECUENCIA (Etapa {k})")
    else:
        print(f"AJUSTE DE LA {k+1}A. ETAPA (Etapa {k})")
    print("-" * 50)
    imprimir_reporte_etapa(resultados_etapas[k], k)
    
    if k < netapas:
        f_dk = next(p["f"] for p in resultados_etapas[k] if p["id"] == f"D{k}")
        print(f"Aplicamos el intervalo de frecuencia: {f_dk:.3f} - {f_intervalo}Hz = {f_ajustes[k+1]:.3f}Hz")
    else:
        print("COMPROBACION FINAL:")
        print(f"  FREC. MIN = {f_d3_et3 if 'f_d3_et3' in locals() else f_nadir:.3f}Hz - {f_intervalo}Hz = {f_min_check:.3f}Hz")
        if es_valido:
            print(f"  Como {f_min_check:.3f}Hz >= {f_min_perm:.3f}Hz (Se respeta la frecuencia minima permisible).")
            print("  Esquema valido. (Check verde [OK])")
        else:
            print(f"  Como {f_min_check:.3f}Hz < {f_min_perm:.3f}Hz (NO se respeta la frecuencia minima permisible).")
            print("  Esquema invalido. (Cruz roja [ERROR])")
    print("\n" + "="*70 + "\n")

# =====================================================================
# 5. GENERACION DE LOS GRAFICOS
# =====================================================================
print("Generando graficos en ventanas independientes...")

plt.style.use('dark_background')

def graficar_escenario(titulo, puntos_list, etapas_lineas):
    plt.figure(titulo, figsize=(10, 6.5))
    
    puntos_t = [p["t"] for p in puntos_list]
    
    # Espectro de colores para tramos de la trayectoria (igual al frontend)
    colores_tramos = ['#ff7b72', '#bc8cff', '#58a6ff', '#56d364', '#d29922', '#388bfd', '#f85149', '#aff5b4']
    
    # Ordenar todos los puntos cronológicamente
    puntos_ordenados = sorted(puntos_list, key=lambda x: x["t"])
    
    # Dibujar la trayectoria por tramos (segmentos) de déficit
    for j in range(1, len(etapas_lineas) + 1):
        start_id = "O" if j == 1 else f"D{j-1}"
        end_id = f"D{j}"
        
        start_pt = next((p for p in puntos_list if p["id"] == start_id), None)
        end_pt = next((p for p in puntos_list if p["id"] == end_id), None)
        
        if start_pt and end_pt:
            t_start = start_pt["t"]
            t_end = end_pt["t"]
            
            # Filtrar los puntos en este tramo temporal
            segment_pts = [p for p in puntos_ordenados if p["t"] >= t_start and p["t"] <= t_end]
            
            if len(segment_pts) > 1:
                seg_t = [p["t"] for p in segment_pts]
                seg_f = [p["f"] for p in segment_pts]
                
                # Déficit de potencia al inicio del tramo
                pct_deficit = int(round(abs(start_pt["p"] * 100)))
                color = colores_tramos[(j - 1) % len(colores_tramos)]
                
                plt.plot(seg_t, seg_f, color=color, linewidth=3.0, 
                         label=f"Tramo {j} (Déficit: {pct_deficit}%)")

    
    for p in puntos_list:
        t, f, desc = p["t"], p["f"], p["id"]
        plt.scatter(t, f, color="red", zorder=5)
        offset_y = 0.08 if "R" in desc else -0.15
        plt.text(t + 0.015, f + offset_y, f"{desc} ({f:.3f} Hz, {t:.3f} s)", 
                 fontsize=9, weight="bold", color="darkred")
            
    colores_lineas = ['orange', 'purple', 'magenta', 'cyan', 'green', 'red', 'yellow', 'brown']
    for idx, (stage_num, f_linea) in enumerate(etapas_lineas.items()):
        color = colores_lineas[idx % len(colores_lineas)]
        plt.axhline(y=f_linea, color=color, linestyle="--", alpha=0.8,
                    label=f"Ajuste Etapa {stage_num} ({f_linea:.3f} Hz)")
        
    plt.axhline(y=f_min_perm, color="red", linestyle="-.", linewidth=1.5, 
                label=f"Frec. Minima Permisible ({f_min_perm:.3f} Hz)")
    
    plt.title(f"Coordinacion de Protecciones - {titulo}", fontsize=11, weight="bold")
    plt.xlabel("Tiempo (segundos)", fontsize=10)
    plt.ylabel("Frecuencia (Hz)", fontsize=10)
    plt.grid(True, which="both", linestyle=":", alpha=0.6)
    plt.legend(loc="upper right", fontsize=9)
    plt.ylim(55.0, 60.5)
    plt.xlim(-0.05, max(puntos_t) + 0.1)

for k in range(1, netapas + 1):
    stages_to_draw = {i: f_ajustes[i] for i in range(1, k + 1)}
    graficar_escenario(f"Etapa {k} - Trayectoria de Calculo", resultados_etapas[k], stages_to_draw)

plt.show()
