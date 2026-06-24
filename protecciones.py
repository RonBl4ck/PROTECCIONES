import numpy as np
import matplotlib.pyplot as plt

# ==========================================
# 1. PREMISAS Y CONFIGURACIÓN DEL SISTEMA
# ==========================================
f0 = 60.00         # Frecuencia inicial (Hz)
H = 3.0            # Constante de inercia (seg)
f_min_perm = 56.00 # Frecuencia mínima permisible (Hz)

# Déficit de potencia inicial (Proceso 3 de la pizarra: -50%)
P_deficit = -0.50 

# Ajustes de las etapas del ERCMF (Frecuencia, Tiempo del relé + interruptor, Carga a aliviar)
etapas = {
    1: {"f_ajuste": 59.000, "delay": 0.4, "alivio": 0.10, "disparado": False, "t_disparo": None},
    2: {"f_ajuste": 58.500, "delay": 0.4, "alivio": 0.20, "disparado": False, "t_disparo": None},
    3: {"f_ajuste": 57.366, "delay": 0.4, "alivio": 0.20, "disparado": False, "t_disparo": None}
}

# Configuración de la simulación temporal
t_max = 1.5        # Tiempo máximo a simular (seg)
dt = 0.001         # Paso de tiempo (1 milisegundo para alta precisión)
tiempos = np.arange(0, t_max, dt)

# Vectores para almacenar los resultados del gráfico
f_historico = []
P_historico = []

f_actual = f0

# ==========================================
# 2. BUCLE DE SIMULACIÓN (ITERACIÓN EN EL TIEMPO)
# ==========================================
for t in tiempos:
    # Evaluar si algún relé se activa al cruzar su frecuencia de ajuste
    for num, e in etapas.items():
        if not e["disparado"] and f_actual <= e["f_ajuste"]:
            e["disparado"] = True
            e["t_disparo"] = t  # Se guarda el momento exacto en que "el relé ve la baja frecuencia"
            print(f"-> Relé Etapa {num} activado en t = {t:.3f} s (f = {f_actual:.3f} Hz)")

    # Evaluar si ya pasaron los 0.4 segundos de delay para desconectar la carga
    for num, e in etapas.items():
        if e["disparado"] and e["alivio"] > 0:
            if t >= (e["t_disparo"] + e["delay"]):
                P_deficit += e["alivio"]  # Se reduce el déficit (se desconecta carga)
                print(f"¡CORTE DE CARGA! Etapa {num} ejecutada en t = {t:.3f} s. Alivio: {e['alivio']*100}%. Nuevo Delta P = {P_deficit:.2f}")
                e["alivio"] = 0  # Para asegurar que se alivie una sola vez

    # Calcular la pendiente (df/dt) con el déficit de potencia actual
    df_dt = (f0 * P_deficit) / (2 * H)
    
    # Si la frecuencia sube y supera los 60Hz, la frenamos en la nominal (estabilización)
    if f_actual >= f0 and df_dt > 0:
        f_actual = f0
    else:
        # Integración numérica simple (Euler) para actualizar la frecuencia
        f_actual += df_dt * dt

    # Guardar datos para graficar
    f_historico.append(f_actual)
    P_historico.append(P_deficit)

# Encontrar el Nadir (punto más bajo alcanzado)
f_nadir = min(f_historico)
t_nadir = tiempos[f_historico.index(f_nadir)]
print(f"\n[RESULTADO] Frecuencia Mínima Alcanzada (Nadir): {f_nadir:.3f} Hz en t = {t_nadir:.3f} s")

# ==========================================
# 3. GENERACIÓN DEL GRÁFICO (MATPLOTLIB)
# ==========================================
plt.figure(figsize=(10, 6))
plt.plot(tiempos, f_historico, label="Evolución de la Frecuencia (f)", color="blue", linewidth=2)

# Líneas de referencia de los ajustes
colors = ['orange', 'purple', 'magenta']
for num, e in etapas.items():
    plt.axhline(y=e["f_ajuste"], color=colors[num-1], linestyle="--", alpha=0.7, 
                label=f"Ajuste Etapa {num} ({e['f_ajuste']} Hz)")

# Línea de frecuencia mínima permitida
plt.axhline(y=f_min_perm, color="red", linestyle="-.", linewidth=1.5, label="Frec. Mínima Permisible (56.00 Hz)")

# Marcar el Nadir en el gráfico
plt.scatter(t_nadir, f_nadir, color='red', zorder=5)
plt.text(t_nadir + 0.03, f_nadir - 0.1, f"Nadir: {f_nadir:.3f} Hz", color='red', weight='bold')

# Estética del gráfico
plt.title("Simulación Dinámica del Rechazo de Carga por Mínima Frecuencia (ERCMF)", fontsize=12, weight='bold')
plt.xlabel("Tiempo (segundos)", fontsize=10)
plt.ylabel("Frecuencia (Hz)", fontsize=10)
plt.grid(True, which='both', linestyle=':', alpha=0.6)
plt.legend(loc="upper right")
plt.ylim(55.5, 60.5)

plt.show()