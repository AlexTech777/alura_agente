## 🤖 Alura Agente

Agente de inteligencia artificial corporativo, abierto a cualquier colaborador de la empresa, capaz de responder preguntas en lenguaje natural sobre la documentación interna de **NimbusFlow**, una plataforma SaaS ficticia de gestión de proyectos.

El agente **comprende y procesa múltiples formatos de archivo** (PDF, Word, Excel, PowerPoint, Markdown, CSV, JSON y HTML), cubriendo distintos dominios de la organización (producto, soporte, precios, estrategia/roadmap, legal y datos/sistemas), usando RAG (Retrieval-Augmented Generation) con LangChain y Gemini. Se despliega en Oracle Cloud Infrastructure (OCI).

## 📐 Arquitectura

```
                 data/  (8 formatos distintos)
   ┌────────────┬────────────┬────────────┬────────────┐
   │  .pdf      │  .docx     │  .xlsx     │  .pptx     │
   │  .md       │  .csv      │  .json     │  .html     │
   └─────┬──────┴─────┬──────┴─────┬──────┴─────┬──────┘
         │            │            │            │
         ▼            ▼            ▼            ▼
   ┌──────────────────────────────────────────────────┐
   │      loaders.py - un lector por cada formato       │
   │   (pypdf, python-docx, openpyxl, python-pptx,      │
   │    csv, json, BeautifulSoup) → texto plano          │
   └─────────────────────┬──────────────────────────────┘
                         ▼
                ┌─────────────────┐
                │  Text Splitter   │  (chunks de ~1000 caracteres, con metadata de origen)
                └────────┬─────────┘
                         ▼
                ┌─────────────────┐
                │ Gemini Embeddings│
                └────────┬─────────┘
                         ▼
                ┌─────────────────┐
                │  Índice FAISS    │  (búsqueda por similitud, único índice para todos los documentos)
                └────────┬─────────┘
                         │
  Usuario ──pregunta──▶  │  ◀── recupera los 4 fragmentos más relevantes (de cualquier formato)
                         ▼
                ┌─────────────────┐
                │  Gemini (LLM)    │  genera la respuesta final
                └────────┬─────────┘
                         ▼
                   Respuesta en
                  lenguaje natural
```

**Componentes:**
- **Carga y procesamiento multi-formato** (`loaders.py`): cada formato tiene su propio lector — `pypdf` (PDF), `python-docx` (Word), `openpyxl` (Excel), `python-pptx` (PowerPoint), lectura directa de texto (Markdown), `csv` (CSV), `json` (JSON) y `BeautifulSoup` (HTML) — y todos devuelven el mismo tipo de objeto (`Document` de LangChain).
- **División en fragmentos**: `RecursiveCharacterTextSplitter` (LangChain) divide los textos extraídos en chunks de ~1000 caracteres.
- **Embeddings**: `GoogleGenerativeAIEmbeddings` convierte cada fragmento en un vector.
- **Vector store**: `FAISS` indexa los vectores de todos los documentos (sin importar su formato original) en un único índice.
- **Generación**: `ChatGoogleGenerativeAI` (Gemini 1.5 Flash) recibe la pregunta + los fragmentos relevantes y genera la respuesta (patrón RAG).
- **Interfaz**: una app Flask (`app.py`) expone el agente como página web y como API JSON, sin restricción de acceso.

## 📁 Estructura del proyecto

```
alura_agente/
├── agent.py                    # Lógica del agente RAG (carga, indexa, responde)
├── loaders.py                  # Un lector por cada formato soportado
├── app.py                      # App web Flask que expone el agente
├── generate_sample_docs.py     # Genera los 8 documentos de ejemplo de NimbusFlow
├── data/
│   ├── base_conocimiento_producto.pdf   # PDF        - Producto
│   ├── faq_soporte.docx                 # Word       - Soporte
│   ├── planes_y_precios.xlsx            # Excel      - Comercial/Precios
│   ├── roadmap_producto.pptx            # PowerPoint - Estratégico
│   ├── terminos_de_uso.md               # Markdown   - Legal
│   ├── tickets_soporte.csv              # CSV        - Calidad/Operacional
│   ├── api_integraciones.json           # JSON       - Datos y Sistemas
│   └── politica_privacidad.html         # HTML       - Legal/Compliance
├── requirements.txt
├── .env.example
└── README.md
```

## 📄 Documentos fuente (uno por formato y dominio)

| Archivo | Formato | Dominio organizacional | Contenido |
|---|---|---|---|
| `base_conocimiento_producto.pdf` | PDF | Producto | Qué es la plataforma, módulos, roles, límites, SLA |
| `faq_soporte.docx` | Word | Soporte | Preguntas frecuentes de soporte técnico |
| `planes_y_precios.xlsx` | Excel | Comercial / Precios | Tabla comparativa de planes, precios, descuentos |
| `roadmap_producto.pptx` | PowerPoint | Estratégico | Roadmap trimestral 2026, métricas objetivo |
| `terminos_de_uso.md` | Markdown | Legal | Términos y condiciones de uso |
| `tickets_soporte.csv` | CSV | Calidad / Operacional | Datos históricos de tickets de soporte |
| `api_integraciones.json` | JSON | Datos y Sistemas | Especificación de la API de integraciones |
| `politica_privacidad.html` | HTML | Legal / Compliance | Política de privacidad y protección de datos |

## 🔑 Requisitos previos

- Python 3.10+
- Una clave de API de **Google Gemini** (gratuita): https://aistudio.google.com/app/apikey

## ▶️ Ejecución local

```bash
git clone <tu-repo>
cd alura_agente

python -m venv venv
source venv/bin/activate        # En Windows: venv\Scripts\activate

pip install -r requirements.txt

cp .env.example .env
# Editá .env y pegá tu clave: GOOGLE_API_KEY=AIza...

python generate_sample_docs.py   # (opcional, ya vienen incluidos)

export $(cat .env | xargs)       # Linux/Mac
python agent.py                  # agente por consola
# o
python app.py                    # app web -> http://localhost:8080
```

> 💡 Para usar tus propios documentos, colocalos en `data/` — el agente detecta la extensión automáticamente. Si cambiás los documentos, borrá `data/faiss_index/` para regenerar el índice.

## 💬 Ejemplos de preguntas y respuestas

| Pregunta | Documento de origen | Respuesta esperada |
|---|---|---|
| ¿Cuántos tableros puedo crear en el plan Free? | PDF | Hasta 3 tableros activos. |
| ¿Cómo recupero mi contraseña? | Word | Con un enlace válido por 30 minutos. |
| ¿Cuánto cuesta el plan Business por usuario? | Excel | 18 USD/mes (mensual) o 15 USD/mes (anual). |
| ¿Qué se planea lanzar en el Q2 2026? | PowerPoint | NimbusFlow AI: resumen automático y asistente conversacional. |
| ¿Cuántos días tengo para pedir un reembolso? | Markdown | 14 días desde el primer pago. |
| ¿Cuál fue la prioridad del ticket T-1005? | CSV | Alta, resuelto en 1.1 horas. |
| ¿Qué header se usa para autenticar la API? | JSON | `X-NimbusFlow-Key`. |
| ¿NimbusFlow vende mis datos a terceros? | HTML | No, no vende datos personales a terceros. |

## ☁️ Deploy en Oracle Cloud Infrastructure (OCI)

### 1. Crear la instancia
1. OCI Console → **Compute → Instances → Create Instance**.
2. Imagen **Ubuntu 22.04** (Always Free: shape `VM.Standard.E2.1.Micro`).
3. Agregá tu clave SSH pública.
4. Asegurate de que tenga **IP pública**.

### 2. Abrir el puerto 8080
VCN → Security Lists → regla de **Ingress**: TCP, puerto `8080`, origen `0.0.0.0/0`.

### 3. Conectarte e instalar dependencias
```bash
ssh -i tu_clave.pem ubuntu@<IP_PUBLICA>
sudo apt update && sudo apt install -y python3-pip python3-venv git
sudo ufw allow 8080
```

### 4. Subir y ejecutar el proyecto
```bash
git clone <tu-repo>
cd alura_agente
python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt
echo "GOOGLE_API_KEY=tu_clave" > .env
export $(cat .env | xargs)
nohup gunicorn -w 2 -b 0.0.0.0:8080 app:app > app.log 2>&1 &
```

### 5. Verificar
Abrí `http://<IP_PUBLICA>:8080` en el navegador.

## 📸 Evidencia del deploy en OCI

*(Reemplazá esta sección con tu captura/video real una vez hecho el deploy)*

🔗 URL pública: `http://<tu-ip-publica>:8080`

![Captura del agente funcionando en OCI](docs/captura_deploy.png)

## ✅ Checklist de entrega

- [x] Repositorio público en GitHub con historial de commits.
- [x] README con descripción, arquitectura, tecnologías, instrucciones y ejemplos.
- [x] Agente funcional en **8 formatos** (PDF, Word, Excel, PowerPoint, Markdown, CSV, JSON, HTML).
- [x] Código para leer y procesar cada formato (`loaders.py`).
- [x] Deploy en OCI Compute, accesible públicamente.
- [ ] Captura/video del deploy agregada al README (pendiente: subir evidencia real).

## 🛠️ Tecnologías usadas

Python · LangChain · pypdf · python-docx · openpyxl · python-pptx · BeautifulSoup · FAISS · Gemini (Google Generative AI) · Flask · Gunicorn · Oracle Cloud Infrastructure (OCI Compute)
