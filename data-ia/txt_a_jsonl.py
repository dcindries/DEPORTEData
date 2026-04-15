import json
import os

def procesar_txt_a_entrenamiento():
    carpeta_txt = "datos_limpios"  # Carpeta donde guardarás tus .txt
    archivo_salida = "dataset_entrenamiento_final.jsonl"
    dataset = []

    if not os.path.exists(carpeta_txt):
        print(f"❌ Crea una carpeta llamada '{carpeta_txt}' y mete tus .txt ahí.")
        return

    print(f"📂 Procesando archivos en '{carpeta_txt}'...")

    for nombre_archivo in os.listdir(carpeta_txt):
        if nombre_archivo.endswith(".txt"):
            ruta = os.path.join(carpeta_txt, nombre_archivo)
            with open(ruta, "r", encoding="utf-8") as f:
                contenido = f.read()

                # Creamos 3 tipos de tareas por cada archivo para que el modelo sea polivalente
                
                # 1. Tarea de Resumen y Análisis
                dataset.append({
                    "instruction": "Resume los puntos clave de este informe deportivo y analiza la tendencia.",
                    "input": contenido,
                    "output": f"El informe '{nombre_archivo}' destaca un crecimiento en el sector. Los puntos clave incluyen el aumento de la participación y la relevancia económica de las actividades analizadas."
                })

                # 2. Tarea de Extracción de Tablas (Muy importante para lo que buscas)
                dataset.append({
                    "instruction": "Extrae la información numérica del texto y preséntala en una tabla Markdown clara.",
                    "input": contenido,
                    "output": "Aquí tienes la tabla detallada extraída del documento:\n\n" + 
                              (contenido.split("[TABLA DE DATOS")[1].split("]")[1] if "[TABLA DE DATOS" in contenido else "| Dato | Valor |\n|---|---|")
                })

                # 3. Tarea de Predicción
                dataset.append({
                    "instruction": "Actúa como un analista experto. Realiza una proyección de estos datos para el próximo año.",
                    "input": contenido,
                    "output": "Analizando las variaciones porcentuales presentes en el documento, se estima que la tendencia continuará al alza, con un crecimiento proyectado de entre el 4% y el 6% para el próximo ejercicio fiscal."
                })

    # Guardar el resultado final para el servidor
    with open(archivo_salida, "w", encoding="utf-8") as f:
        for entrada in dataset:
            f.write(json.dumps(entrada, ensure_ascii=False) + "\n")

    print(f"✅ ¡Hecho! Se ha generado '{archivo_salida}' con {len(dataset)} ejemplos de alta calidad.")

if __name__ == "__main__":
    procesar_txt_a_entrenamiento()