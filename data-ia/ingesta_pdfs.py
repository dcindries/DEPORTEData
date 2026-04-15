import os
import fitz  # PyMuPDF
import chromadb
import json

def limpiar_y_formatear_tabla(datos):
    """
    Toma los datos crudos extraídos de una tabla y aplica técnicas de 
    Data Science para limpiarlos y evitar filas/columnas fantasma.
    """
    if not datos:
        return ""
    
    # 1. Limpieza básica: quitar saltos de línea y None
    filas_limpias = []
    for fila in datos:
        fila_limpia = [str(celda).replace("\n", " ").strip() if celda is not None else "" for celda in fila]
        filas_limpias.append(fila_limpia)
        
    # 2. Eliminar filas completamente vacías
    filas_con_datos = [f for f in filas_limpias if any(c != "" for c in f)]
    if not filas_con_datos:
        return ""
        
    # 3. Eliminar columnas completamente vacías
    num_cols = len(filas_con_datos[0])
    cols_a_mantener = []
    for col_idx in range(num_cols):
        if any(fila[col_idx] != "" for fila in filas_con_datos):
            cols_a_mantener.append(col_idx)
            
    # Creamos la tabla final solo con las columnas "vivas"
    tabla_final = []
    for fila in filas_con_datos:
        tabla_final.append([fila[i] for i in cols_a_mantener])
        
    if not tabla_final or not tabla_final[0]:
        return ""
        
    # 4. Proteger caracteres Markdown (si hay '|' rompe la tabla, lo cambiamos a '/')
    tabla_final = [[c.replace("|", "/") for c in f] for f in tabla_final]
    
    md = ""
    cabecera = tabla_final[0]
    # Rellenar nombres de columna vacíos para que las LLM no se confundan
    cabecera = [c if c else f"Col_{i+1}" for i, c in enumerate(cabecera)]
    
    # Formateo de la cabecera
    md += "| " + " | ".join(cabecera) + " |\n"
    md += "|" + "|".join(["---"] * len(cabecera)) + "|\n"
    
    # Formateo del cuerpo
    for fila in tabla_final[1:]:
        # Igualar el número de celdas a la cabecera por si la tabla venía "abierta"
        if len(fila) < len(cabecera):
            fila.extend([""] * (len(cabecera) - len(fila)))
        elif len(fila) > len(cabecera):
            fila = fila[:len(cabecera)]
            
        md += "| " + " | ".join(fila) + " |\n"
        
    return md

def extraer_texto_pdf(ruta_pdf):
    """Abre el PDF y extrae el texto de todas sus páginas, detectando tablas y formateándolas."""
    doc = fitz.open(ruta_pdf)
    texto_completo = ""
    
    for pagina in doc:
        try:
            # Busca tablas en la página (disponible en versiones recientes de PyMuPDF)
            tablas_lista = list(pagina.find_tables())
            rects_tablas = [fitz.Rect(tabla.bbox) for tabla in tablas_lista]
            
            # Obtenemos los bloques de texto
            bloques = pagina.get_text("blocks")
            texto_pagina = ""
            
            # Incorporamos el texto que no interseca con las tablas detectadas para no duplicarlo
            for bloque in bloques:
                rect_bloque = fitz.Rect(bloque[:4])
                es_tabla = any(rect_bloque.intersects(r) for r in rects_tablas)
                
                if not es_tabla:
                    texto_pagina += bloque[4] + "\n"
            
            # Si detectamos tablas, las añadimos formateadas en Markdown (ideal para RAG)
            if tablas_lista:
                texto_pagina += "\n\n[INICIO DE TABLA]\n"
                for tabla in tablas_lista:
                    datos = tabla.extract()
                    md_tabla = limpiar_y_formatear_tabla(datos)
                    if md_tabla:
                        texto_pagina += md_tabla + "\n"
                texto_pagina += "[FIN DE TABLA]\n\n"
                
            texto_completo += texto_pagina
            
        except AttributeError:
            # Fallback en caso de usar una versión antigua de PyMuPDF sin 'find_tables'
            texto_completo += pagina.get_text("text") + "\n"
            
    return texto_completo

def dividir_en_chunks(texto, tamaño=1000, solapamiento=200):
    """Divide el texto largo en trozos que se solapan para no perder contexto."""
    chunks = []
    inicio = 0
    while inicio < len(texto):
        fin = inicio + tamaño
        # Extraemos el fragmento
        chunk = texto[inicio:fin]
        # Limpiamos dobles espacios y saltos de línea raros del PDF
        chunk = " ".join(chunk.split())
        chunks.append(chunk)
        inicio += tamaño - solapamiento
    return chunks

def crear_bd_desde_pdfs(directorio_pdfs, directorio_json):
    # 1. Configurar ChromaDB
    # Subimos un nivel desde la carpeta 'pdfs' a la raíz del proyecto
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    db_path = os.path.join(base_dir, "mi_bd_chroma")
    
    client = chromadb.PersistentClient(path=db_path)
    nombre_coleccion = "datos_deportivos"
    
    try:
        client.delete_collection(nombre_coleccion)
        print("🧹 Colección de ChromaDB anterior borrada para evitar duplicados.")
    except:
        pass
        
    coleccion = client.create_collection(name=nombre_coleccion)

    # Crear la carpeta data_json si no existe
    os.makedirs(directorio_json, exist_ok=True)

    # 2. Buscar todos los PDFs en la carpeta data/
    if not os.path.exists(directorio_pdfs):
        print(f"⚠️ No se encontró el directorio de origen: {directorio_pdfs}")
        return

    archivos_pdf = [f for f in os.listdir(directorio_pdfs) if f.endswith('.pdf')]
    
    if not archivos_pdf:
        print(f"⚠️ No se encontraron archivos PDF en la ruta: {directorio_pdfs}")
        return

    print(f"📚 Se encontraron {len(archivos_pdf)} archivos PDF. Iniciando lectura...\n")
    total_chunks = 0

    # 3. Procesar cada archivo
    for archivo in archivos_pdf:
        ruta_pdf = os.path.join(directorio_pdfs, archivo)
        print(f"📄 Leyendo: {archivo} ...")
        
        texto_puro = extraer_texto_pdf(ruta_pdf)
        fragmentos = dividir_en_chunks(texto_puro, tamaño=1000, solapamiento=200)
        
        ids = []
        documentos = []
        metadatos = []
        
        # Para guardar los datos en JSON
        chunks_para_json = []
        
        for i, fragmento in enumerate(fragmentos):
            # Ignorar fragmentos que sean muy cortos (ej. una página en blanco)
            if len(fragmento) < 50:
                continue
                
            ids.append(f"{archivo}_chunk_{i}")
            documentos.append(fragmento)
            metadatos.append({"fuente": archivo, "chunk": i})
            
            chunks_para_json.append({
                "chunk_id": f"{archivo}_chunk_{i}",
                "texto": fragmento,
                "fuente": archivo
            })
            
        # 4. Guardar los datos extraídos en la carpeta data_json
        nombre_sin_ext = os.path.splitext(archivo)[0]
        ruta_json = os.path.join(directorio_json, f"{nombre_sin_ext}.json")
        
        with open(ruta_json, "w", encoding="utf-8") as f:
            json.dump({
                "archivo_origen": archivo,
                "total_chunks": len(chunks_para_json),
                "chunks": chunks_para_json
            }, f, indent=4, ensure_ascii=False)
            
        print(f"   💾 Datos guardados en JSON: {ruta_json}")

        # 5. Guardar los fragmentos de este PDF en ChromaDB
        if documentos:
            coleccion.add(
                documents=documentos,
                ids=ids,
                metadatas=metadatos
            )
            total_chunks += len(documentos)
            print(f"   ✅ Se guardaron {len(documentos)} fragmentos en ChromaDB.")

    print(f"\n🎉 ¡Proceso completado! Base de datos y JSON actualizados ({total_chunks} fragmentos totales).")

if __name__ == "__main__":
    # Aseguramos apuntar a las carpetas correctas desde la raíz del proyecto
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    DIR_DATA = os.path.join(BASE_DIR, "data")
    DIR_JSON = os.path.join(BASE_DIR, "data_json")
    
    # Creamos 'data' por si acaso, para evitar errores si no existe
    os.makedirs(DIR_DATA, exist_ok=True)
    
    crear_bd_desde_pdfs(directorio_pdfs=DIR_DATA, directorio_json=DIR_JSON)