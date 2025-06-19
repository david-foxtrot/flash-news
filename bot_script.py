# bot_script.py

import os
import json
import requests
from datetime import datetime
from dotenv import load_dotenv
import pathlib

# Cargar las variables de entorno (nuestras claves secretas) del archivo .env
# Este comando busca un archivo llamado .env en la misma carpeta.
load_dotenv()

# --- CONFIGURACIÓN Y CLAVES SECRETAS ---
# Obtenemos las claves de forma segura del archivo .env
# Si no encuentra el archivo .env, usará None como valor por defecto.
LLM_API_KEY = os.getenv("LLM_API_KEY")
NEWS_API_KEY = os.getenv("NEWS_API_KEY") 

# Directorio donde se guardarán las noticias individuales
CONTENT_DIR = pathlib.Path("src/content/news")

# --- PROMPT V7: "ANALISTA ESTRATÉGICO" ---
PROMPT_V7 = """
### ROL Y OBJETIVO ###
Eres "Pulse", el Editor Jefe de una agencia de noticias digital global, reconocido por tu aguda perspicacia analítica. Tu especialidad es transformar información cruda en alertas de última hora que no solo informan, sino que explican la importancia de los eventos de manera clara, concisa y de alto impacto.

### PASOS PREVIOS DE PROCESAMIENTO Y LIMPIEZA ###
1.  **TRADUCCIÓN OBLIGATORIA A ESPAÑOL:** Si el texto de entrada no está en español, tradúcelo íntegramente a un español latinoamericano neutro.
2.  **LIMPIEZA DE CONTENIDO:** Elimina por completo hipervínculos (URLs), citas de fuentes (como [1] o (Reuters)) y cualquier otro metadato.

### REGLAS DE ORO Y ESTILO ###
1.  **PRINCIPIO GUÍA: "QUÉ" Y "POR QUÉ".** No te limites a describir QUÉ pasó. Tu valor principal es explicar POR QUÉ es importante.
2.  **LONGITUD MÁXIMA:** La salida final COMPLETA nunca debe superar los 270 caracteres.
3.  **EMOJIS:** Usa únicamente las banderas de los 2-3 países protagonistas. Prohibido cualquier otro emoji.
4.  **CLARIDAD MÁXIMA:** Usa una o dos frases cortas. Prioriza siempre la legibilidad.
5.  **LENGUAJE ANALÍTICO:** Utiliza un lenguaje que denote análisis, no solo descripción (ej: "buscando...", "lo que marca un...", "en una demostración de...", "afirmando que...").

### PROCESO DE ANÁLISIS Y SÍNTESIS ###
1.  **Identifica Países Protagonistas:** Extrae las banderas de los 2 o 3 actores más importantes.
    * **Condición:** Si no hay países, omite las banderas y el separador "|".
2.  **Crea un Flujo Narrativo Analítico:**
    * **Frase 1 (El Hecho Decisivo):** Establece el evento principal de forma directa y contundente.
    * **Frase 2 (El Significado Estratégico):** Responde a la pregunta: **¿Cuál es el propósito o la implicación de esta acción?** Explica su significado, el mensaje que envía o la nueva dinámica que establece en el conflicto.
3.  **Elige una Palabra Clave:** Selecciona la más apropiada: **URGENTE, ALERTA, OFICIAL, CLAVE.**

### ESTRUCTURA DE SALIDA ###
`[EMOJIS DE BANDERAS] | [PALABRA CLAVE]: [FRASE 1 CON EL HECHO DECISIVO]. [FRASE 2 CON EL SIGNIFICADO ESTRATÉGICO].`

---
AHORA, PROCESA LA SIGUIENTE NOTICIA BAJO ESTAS REGLAS DE ESTILO:
"""

# --- FUNCIONES DEL BOT ---

def get_latest_news():
    """
    Obtiene las últimas noticias de una API.
    Por ahora, devuelve una noticia de prueba para testear.
    """
    print("1. Obteniendo noticias (usando datos de prueba)...")
    # TODO: Cuando estés listo, reemplaza esto con una llamada real a una News API
    # Ejemplo: url = f"https://newsapi.org/v2/top-headlines?country=us&apiKey={NEWS_API_KEY}"
    # response = requests.get(url)
    # articles = response.json()['articles']
    # return articles[0] 
    
    return {
        "title": "La Guardia Revolucionaria de Irán anunció el lanzamiento de misiles hipersónicos contra Israel",
        "content": "En el evento de presentación, un cartel gigante fue instalado en Teherán con un mensaje escrito en hebreo: “400 segundos hasta Tel Aviv”. Según la información difundida por medios estatales, los misiles lanzados durante esta oleada tienen un alcance operativo estimado de 1.400 kilómetros y son capaces de transportar cargas útiles de hasta 450 kilogramos. El IRGC calificó a los Fattah-1 como “poderosos y altamente maniobrables”, y aseguró que estos proyectiles “perforaron el escudo antimisiles” israelí...",
        "url": "https://www.infobae.com/ejemplo-de-noticia-final"
    }

def process_with_llm(article_content):
    """
    Envía el contenido de la noticia al LLM especificado en Google AI Studio.
    """
    print(f"2. Procesando con la IA (Modelo: gemma-3-4b-it en Google AI Studio)...")
    if not LLM_API_KEY:
        print("Error Crítico: La clave de API del LLM (LLM_API_KEY) no está configurada en el archivo .env")
        return None
        
    model_name = "gemma-3-4b-it" 
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent?key={LLM_API_KEY}"
    
    payload = {"contents": [{"parts": [{"text": PROMPT_V7 + article_content}]}]}
    headers = {'Content-Type': 'application/json'}
    
    try:
        response = requests.post(url, json=payload, headers=headers)
        response.raise_for_status()
        data = response.json()
        
        if not data.get('candidates'):
            print(f"Error: La respuesta de la IA no contiene 'candidates'. Revisa si el nombre del modelo '{model_name}' es correcto para tu API Key. Respuesta completa: {data}")
            return None

        raw_text = data['candidates'][0]['content']['parts'][0]['text']
        
        # Parseo robusto del texto de respuesta
        if '|' not in raw_text or ':' not in raw_text:
            print(f"Error: La IA devolvió un formato inesperado: {raw_text}")
            return None

        parts = raw_text.split('|', 1)
        flags = parts[0].strip()
        keyword_and_sentences = parts[1].split(':', 1)
        
        keyword = keyword_and_sentences[0].strip()
        sentences_combined = keyword_and_sentences[1].strip()
        sentence_parts = [s.strip() for s in sentences_combined.split('.') if s.strip()]
        
        sentence1 = (sentence_parts[0] + ".") if len(sentence_parts) > 0 else ""
        sentence2 = (sentence_parts[1] + ".") if len(sentence_parts) > 1 else ""

        return {"flags": flags, "keyword": keyword, "sentence1": sentence1, "sentence2": sentence2}
        
    except requests.exceptions.RequestException as e:
        print(f"Error llamando a la API de Google: {e}")
        if 'response' in locals():
            print(f"Código de estado: {response.status_code}")
            print(f"Respuesta del servidor: {response.text}")
        return None

def save_new_article(article_data, original_url):
    """
    Guarda la nueva noticia como un archivo JSON individual en el directorio de contenido.
    """
    print(f"3. Guardando la nueva noticia...")
    
    CONTENT_DIR.mkdir(parents=True, exist_ok=True)
    
    timestamp = datetime.utcnow()
    new_entry_id = timestamp.strftime('%Y%m%d%H%M%S')
    
    new_entry_data = {
        "id": new_entry_id,
        "timestamp": timestamp.isoformat() + "Z",
        "flags": article_data['flags'],
        "keyword": article_data['keyword'],
        "sentence1": article_data['sentence1'],
        "sentence2": article_data['sentence2'],
        "source_url": original_url
    }

    file_name = f"{new_entry_id}.json"
    file_path = CONTENT_DIR / file_name

    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(new_entry_data, f, indent=2, ensure_ascii=False)
    
    print(f"¡Noticia guardada con éxito en {file_path}!")

# --- FLUJO PRINCIPAL DE EJECUCIÓN ---
if __name__ == "__main__":
    print("--- Iniciando el Bot de Noticias ---")
    latest_article = get_latest_news()
    if latest_article:
        processed_data = process_with_llm(latest_article['content'])
        if processed_data:
            save_new_article(processed_data, latest_article['url'])
    print("--- Bot ha finalizado su ejecución ---")